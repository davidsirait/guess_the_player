"""
Session-based game API endpoints
Provides stateful gameplay with score tracking and cheat prevention
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

from app.models.schemas import (
    SessionStartRequest,
    SessionStartResponse,
    SessionGuessRequest,
    SessionGuessResponse,
    SessionNextQuestionRequest,
    SessionNextQuestionResponse,
    SessionEndResponse
)
from app.services.session_service import SessionService
from app.dependencies import get_session_service

router = APIRouter(prefix="/session", tags=["session"])


def validate_session_id(session_id: str) -> str:
    """Validate that session_id is a valid UUID"""
    try:
        uuid.UUID(session_id)
        return session_id
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid session ID format"
        )


@router.post("/start", response_model=SessionStartResponse)
def start_session(
    request: SessionStartRequest,
    session_service: SessionService = Depends(get_session_service)
):
    """
    Start a new game session
    
    Creates a new session with first question and returns session ID.
    Use this session ID for all subsequent guesses.
    
    Args:
        request: Contains difficulty level and top_n players
        
    Returns:
        Session ID, first question, and initial score
        
    Raises:
        HTTPException: 400 if invalid difficulty or top_n out of range
    """
    try:
        result = session_service.create_session(request.difficulty, request.top_n)
        return SessionStartResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        # Log but don't expose internal errors
        print(f"Error creating session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error creating session"
        )


@router.post("/{session_id}/guess", response_model=SessionGuessResponse)
@limiter.limit("10/minute")
def submit_guess(
    request: Request,
    session_id: str,
    guess_request: SessionGuessRequest,
    session_service: SessionService = Depends(get_session_service)
):
    """
    Submit a guess for the current question in session
    
    Rate limited to 10 guesses per minute per IP to prevent abuse.
    
    Validates that guess is for the current question in the session,
    preventing cheating by guessing for different players.
    
    Args:
        request: FastAPI request object (for rate limiting)
        session_id: Session identifier (UUID format)
        guess_request: Contains player name guess
        
    Returns:
        Result with correctness, answer, score, and similarity
        
    Raises:
        HTTPException: 404 if session not found, 400 if invalid session ID or no active question, 429 if rate limit exceeded
    """
    # Validate session ID format
    validate_session_id(session_id)
    
    try:
        result = session_service.submit_guess(session_id, guess_request.guess)
        return SessionGuessResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error submitting guess: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error submitting guess"
        )


@router.post("/{session_id}/next", response_model=SessionNextQuestionResponse)
def get_next_question(
    session_id: str,
    request: SessionNextQuestionRequest = SessionNextQuestionRequest(),
    session_service: SessionService = Depends(get_session_service)
):
    """
    Get the next question in the session
    
    Call this after a guess to move to the next question.
    Difficulty and top_n are OPTIONAL:
    - If not provided: Uses the values from session start (or last /next call)
    - If provided: Uses new values and updates session defaults for future questions
    
    Examples:
    1. Keep same difficulty: POST {} or no body
    2. Change difficulty: POST {"difficulty": "moderate"}
    3. Change both: POST {"difficulty": "long", "top_n": 500}
    
    Args:
        session_id: Session identifier (UUID format)
        request: Optional difficulty/top_n overrides
        
    Returns:
        New question with current session score
        
    Raises:
        HTTPException: 404 if session not found, 400 if invalid session ID
    """
    # Validate session ID format
    validate_session_id(session_id)
    
    try:
        result = session_service.get_next_question(
            session_id, 
            request.difficulty, 
            request.top_n
        )
        return SessionNextQuestionResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting next question: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error getting next question"
        )


@router.delete("/{session_id}", response_model=SessionEndResponse)
def end_session(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """
    End a game session and get final statistics
    
    Deletes the session and returns final score, accuracy, and duration.
    
    Args:
        session_id: Session identifier (UUID format)
        
    Returns:
        Final session statistics
        
    Raises:
        HTTPException: 404 if session not found, 400 if invalid session ID
    """
    # Validate session ID format
    validate_session_id(session_id)
    
    try:
        result = session_service.end_session(session_id)
        return SessionEndResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error ending session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error ending session"
        )


@router.get("/{session_id}/status")
def get_session_status(
    session_id: str,
    session_service: SessionService = Depends(get_session_service)
):
    """
    Get current session status without affecting the game
    
    Useful for checking score, attempts, and session info.
    
    Args:
        session_id: Session identifier (UUID format)
        
    Returns:
        Current session data
        
    Raises:
        HTTPException: 404 if session not found, 400 if invalid session ID
    """
    # Validate session ID format
    validate_session_id(session_id)
    
    try:
        session_data = session_service.get_session(session_id)
        # Don't expose internal player_id
        return {
            "session_id": session_data["session_id"],
            "score": session_data["score"],
            "total_attempts": session_data["total_attempts"],
            "correct_guesses": session_data["correct_guesses"],
            "created_at": session_data["created_at"],
            "last_activity": session_data["last_activity"]
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting session status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error getting session status"
        )