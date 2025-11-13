"""
Business logic for the career sequence game
"""

import json
from typing import Optional, Tuple, List
from fastapi import HTTPException

from app.models.schemas import Question, GuessResponse, PlayerLookupResponse, Club, StatsResponse, DifficultyStats
from app.services.database import execute_query, execute_query_one
from app.utils.fuzzy_match import fuzzy_match_player
from app.config import get_settings


class GameService:
    """Service for game-related operations"""
    
    @staticmethod
    def get_random_question(difficulty: str, top_n: int = 200) -> Question:
        """
        Get a random question by career length and top n players by market value
        
        Args:
            difficulty: 'short', 'moderate', or 'long'
            top_n : Limit to top N players by market value
            
        Returns:
            Question object
            
        Raises:
            HTTPException: If difficulty invalid or no questions available
        """
        if difficulty not in ['short', 'moderate', 'long']:
            raise HTTPException(
                status_code=400,
                detail="Career length must be 'short', 'moderate', or 'long'"
            )
        
        query = """
            with player_cte AS(
                SELECT 
                    player_id,
                    difficulty,
                    ROW_NUMBER () OVER (ORDER BY market_value_numeric DESC) AS rn,
                    num_moves,
                    num_players_with_same_seq as shared_by,
                    club_jsons
                FROM sequence_analysis
                WHERE TRUE
                ORDER BY market_value_numeric DESC
            )
            SELECT 
                player_id,
                difficulty,
                num_moves,
                shared_by,
                club_jsons    
            FROM player_cte 
            WHERE rn <= ?
            AND difficulty = ?
            ORDER BY RANDOM()
            LIMIT 1;
        """
        
        result = execute_query_one(query, [top_n, difficulty])
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No questions available for top {top_n} players with career length {difficulty}"
            )
        
        player_id, diff, num_moves, shared_by, clubs_json = result
        clubs = json.loads(clubs_json) if clubs_json else []
        
        return Question(
            player_id=player_id,
            difficulty=diff,
            num_moves=num_moves,
            shared_by=shared_by,
            clubs=[Club(**club) for club in clubs]
        )
    
    @staticmethod
    def check_guess(player_id: str, guess: str) -> GuessResponse:
        """
        Check if a player guess is correct
        
        Args:
            player_id: ID of the player to guess
            guess: Player name guess
            
        Returns:
            GuessResponse with correctness and details
            
        Raises:
            HTTPException: If player not found
        """
        settings = get_settings()
        
        # Get the correct answer
        query = """
            SELECT 
                player_name, 
                sequence_string
            FROM sequence_analysis
            WHERE player_id = ?
        """
        
        result = execute_query_one(query, [player_id])
        
        if not result:
            raise HTTPException(status_code=404, detail="Player not found")
        
        correct_player_name, sequence_string = result
        
        # Find all players with the same sequence
        all_answers_query = """
            SELECT player_name
            FROM sequence_analysis
            WHERE sequence_string = ?
        """
        
        all_answers = execute_query(all_answers_query, [sequence_string])
        all_possible_names = [name[0] for name in all_answers]
        
        # Check exact match first
        guess_clean = guess.strip().lower()
        for name in all_possible_names:
            if guess_clean == name.lower():
                return GuessResponse(
                    correct=True,
                    actual_answer=correct_player_name,
                    similarity_score=100,
                    all_possible_answers=all_possible_names
                )
        
        # Fuzzy match
        matched_name, score = fuzzy_match_player(guess, all_possible_names)
        print(score)
        is_correct = score >= settings.fuzzy_match_threshold
        
        return GuessResponse(
            correct=is_correct,
            actual_answer=correct_player_name,
            similarity_score=score,
            all_possible_answers=all_possible_names
        )
    
    @staticmethod
    def lookup_player(player_name: str) -> PlayerLookupResponse:
        """
        Lookup a player by name (with fuzzy matching)
        
        Args:
            player_name: Player name to search for
            
        Returns:
            PlayerLookupResponse with player details
            
        Raises:
            HTTPException: If player not found
        """
        settings = get_settings()
        
        # Get all players for fuzzy matching
        all_players_query = """
            SELECT player_id, player_name
            FROM sequence_analysis
        """
        
        all_players = execute_query(all_players_query)
        player_names = {name: pid for pid, name in all_players}
        
        # Fuzzy match
        matched_name, score = fuzzy_match_player(
            player_name,
            list(player_names.keys())
        )
        
        if score < settings.player_lookup_threshold:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player_id = player_names[matched_name]
        
        # Get player data
        query = """
            SELECT 
                player_id,
                player_name,
                num_moves,
                club_jsons
            FROM sequence_analysis
            WHERE player_id = ?
        """
        
        result = execute_query_one(query, [player_id])
        
        if not result:
            raise HTTPException(status_code=404, detail="Player not found")
        
        pid, pname, num_moves, clubs_json = result
        clubs = json.loads(clubs_json) if clubs_json else []
        
        return PlayerLookupResponse(
            player_id=pid,
            player_name=pname,
            num_moves=num_moves,
            clubs=[Club(**club) for club in clubs]
        )
    
    @staticmethod
    def get_statistics() -> StatsResponse:
        """
        Get game statistics
        
        Returns:
            StatsResponse with game statistics
        """
        stats_query = """
            SELECT 
                difficulty,
                COUNT(*) as count,
                ROUND(AVG(num_moves), 2) as avg_moves,
                MIN(num_moves) as min_moves,
                MAX(num_moves) as max_moves
            FROM sequence_analysis
            GROUP BY difficulty
        """
        
        total_query = "SELECT COUNT(*) FROM sequence_analysis"
        
        stats = execute_query(stats_query)
        total = execute_query_one(total_query)[0]
        
        return StatsResponse(
            total_questions=total,
            by_difficulty=[
                DifficultyStats(
                    difficulty=row[0],
                    count=row[1],
                    avg_moves=row[2],
                    min_moves=row[3],
                    max_moves=row[4]
                )
                for row in stats
            ]
        )