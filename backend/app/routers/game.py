"""
Game-related API endpoints
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import Question, GuessRequest, GuessResponse, StatsResponse
from app.services.game_service import GameService

router = APIRouter(prefix="/game", tags=["game"])


@router.get("/question/{difficulty}", response_model=Question)
def get_question(difficulty: str):
    """
    Get a random question by difficulty level
    
    Args:
        difficulty: 'easy', 'medium', or 'hard'
        
    Returns:
        Question with club sequence (player name hidden)
        
    Raises:
        HTTPException: 400 if invalid difficulty, 404 if no questions available
    """
    try:
        return GameService.get_random_question(difficulty)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting question: {str(e)}")


@router.post("/guess", response_model=GuessResponse)
def check_guess(guess_request: GuessRequest):
    """
    Check if a player guess is correct
    
    Args:
        guess_request: Contains player_id and player name guess
        
    Returns:
        Result with correctness, actual answer, similarity score, and all possible answers
        
    Raises:
        HTTPException: 404 if player not found, 500 for other errors
    """
    try:
        return GameService.check_guess(
            guess_request.player_id,
            guess_request.guess
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking guess: {str(e)}")


@router.get("/stats", response_model=StatsResponse)
def get_stats():
    """
    Get game statistics
    
    Returns:
        Statistics about available questions by difficulty
        
    Raises:
        HTTPException: 500 if error retrieving stats
    """
    try:
        return GameService.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")