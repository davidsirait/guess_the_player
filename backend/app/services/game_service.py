"""
Business logic for the career sequence game
"""

import json
import re
from typing import Optional, Tuple, List
from fastapi import HTTPException

from app.models.schemas import Question, GuessResponse, PlayerLookupResponse, Club, StatsResponse, DifficultyStats
from app.services.database import execute_query, execute_query_one
from app.utils.fuzzy_match import fuzzy_match_player
from app.utils.image_helpers import get_player_image_url, get_club_image_url, extract_club_id_from_url
from app.config import get_settings


def sanitize_guess(guess: str) -> str:
    """Sanitize user input for player name guesses"""
    if not guess:
        return ""
    
    # Strip whitespace
    guess = guess.strip()
    
    # Remove excessive whitespace
    guess = re.sub(r'\s+', ' ', guess)
    
    # Remove special characters except hyphens, apostrophes, and spaces
    guess = re.sub(r'[^\w\s\'-]', '', guess)
    
    return guess


class GameService:
    """Service for game-related operations"""
    
    @staticmethod
    def get_random_question(difficulty: str, top_n: int = 200) -> Question:
        """
        Get a random question by career length and top n players by market value
        
        Args:
            difficulty: 'short', 'moderate', or 'long'
            top_n: Limit to top N players by market value (max 5000)
            
        Returns:
            Question object
            
        Raises:
            HTTPException: If difficulty invalid or no questions available
        """

        # load settings 
        settings = get_settings()

        # Validate difficulty
        if difficulty not in ['short', 'moderate', 'long']:
            raise HTTPException(
                status_code=400,
                detail="Career length must be 'short', 'moderate', or 'long'"
            )
        
        # Validate and cap top_n
        top_n = max(1, min(top_n, 5000))
        
        query = """
            with player_cte AS(
                SELECT 
                    player_name,
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
                player_name,
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
        
        try:
            result = execute_query_one(query, [top_n, difficulty])
        except Exception as e:
            # Log error but don't expose internals
            print(f"Database error in get_random_question: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error retrieving question"
            )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No questions available for top {top_n} players with career length {difficulty}"
            )
        
        player_name, player_id, diff, num_moves, shared_by, clubs_json = result
        clubs = json.loads(clubs_json) if clubs_json else []

        # only for debugging purpose
        if settings.environment == "dev":
            print(f"Selected player for question: {player_name} (ID: {player_id})")
        
        # Process clubs to add fallback images
        processed_clubs = []
        for club in clubs:
            club_id = extract_club_id_from_url(club.get('logo', ''))
            processed_clubs.append(Club(
                club=club.get('club', ''),
                logo=get_club_image_url(club_id, club.get('logo', '')),
                season=club.get('season', '')
            ))
        
        return Question(
            player_id=player_id,
            difficulty=diff,
            num_moves=num_moves,
            shared_by=shared_by,
            clubs=processed_clubs
        )
    
    @staticmethod
    def check_guess(player_id: str, guess: str) -> GuessResponse:
        """
        Check if a player guess is correct
        
        Args:
            player_id: ID of the player to guess
            guess: Player name guess (will be sanitized)
            
        Returns:
            GuessResponse with correctness and details
            
        Raises:
            HTTPException: If player not found
        """
        settings = get_settings()
        
        # Sanitize the guess
        guess = sanitize_guess(guess)
        
        if not guess:
            raise HTTPException(
                status_code=400,
                detail="Guess cannot be empty"
            )
        
        # Get the correct answer
        query = """
            SELECT 
                a.player_name,
                b.player_img_url, 
                a.sequence_string
            FROM sequence_analysis AS a
            LEFT JOIN players AS b ON a.player_id = b.player_id
            WHERE a.player_id = ?
        """
        
        try:
            result = execute_query_one(query, [player_id])
        except Exception as e:
            print(f"Database error in check_guess: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error checking guess"
            )
        
        if not result:
            raise HTTPException(status_code=404, detail="Player not found")
        
        correct_player_name, correct_player_img_url, sequence_string = result
        
        # Find all players with the same sequence
        all_answers_query = """
            SELECT 
                a.player_name,
                b.player_img_url, 
                a.sequence_string
            FROM sequence_analysis AS a
            LEFT JOIN players AS b ON a.player_id = b.player_id
            WHERE a.sequence_string = ?
        """
        
        try:
            all_answers = execute_query(all_answers_query, [sequence_string])
        except Exception as e:
            print(f"Database error getting all answers: {e}")
            # Continue with just the main answer
            all_answers = [(correct_player_name, correct_player_img_url, sequence_string)]
        
        all_possible_names = [name[0] for name in all_answers]
        all_possible_names_img_urls = [
            get_player_image_url(player_id, name[1] if name[1] else "") 
            for name in all_answers
        ]
        
        # Get the correct player's image with fallback
        correct_player_img_url = get_player_image_url(player_id, correct_player_img_url)
        
        # Check exact match first (case-insensitive)
        guess_clean = guess.strip().lower()
        for name in all_possible_names:
            if guess_clean == name.lower():
                return GuessResponse(
                    correct=True,
                    actual_answer=correct_player_name,
                    actual_answer_img_url=correct_player_img_url,
                    similarity_score=100.0,
                    all_possible_answers=all_possible_names,
                    all_possible_answers_img_urls=all_possible_names_img_urls
                )
        
        # Fuzzy match
        matched_name, score = fuzzy_match_player(guess, all_possible_names)
        is_correct = score >= settings.fuzzy_match_threshold
        
        return GuessResponse(
            correct=is_correct,
            actual_answer=correct_player_name,
            actual_answer_img_url=correct_player_img_url,
            similarity_score=score,
            all_possible_answers=all_possible_names,
            all_possible_answers_img_urls=all_possible_names_img_urls
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
        
        # Sanitize input
        player_name = sanitize_guess(player_name)
        
        if not player_name:
            raise HTTPException(
                status_code=400,
                detail="Player name cannot be empty"
            )
        
        # Get all players for fuzzy matching
        all_players_query = """
            SELECT player_id, player_name
            FROM sequence_analysis
        """
        
        try:
            all_players = execute_query(all_players_query)
        except Exception as e:
            print(f"Database error in lookup_player: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error looking up player"
            )
        
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
        
        try:
            result = execute_query_one(query, [player_id])
        except Exception as e:
            print(f"Database error getting player data: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error retrieving player data"
            )
        
        if not result:
            raise HTTPException(status_code=404, detail="Player not found")
        
        pid, pname, num_moves, clubs_json = result
        clubs = json.loads(clubs_json) if clubs_json else []
        
        # Process clubs to add fallback images
        processed_clubs = []
        for club in clubs:
            club_id = extract_club_id_from_url(club.get('logo', ''))
            processed_clubs.append(Club(
                club=club.get('club', ''),
                logo=get_club_image_url(club_id, club.get('logo', '')),
                season=club.get('season', '')
            ))
        
        return PlayerLookupResponse(
            player_id=pid,
            player_name=pname,
            num_moves=num_moves,
            clubs=processed_clubs
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
        
        try:
            stats = execute_query(stats_query)
            total = execute_query_one(total_query)[0]
        except Exception as e:
            print(f"Database error in get_statistics: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error retrieving statistics"
            )
        
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