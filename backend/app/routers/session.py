"""
Session-based game API endpoints
Provides stateful gameplay with score tracking and cheat prevention
"""

from fastapi import APIRouter, HTTPException, Depends

from app.models.schemas import (
    SessionStartRequest,
    SessionStartResponse,
    SessionGuessRequest,
    SessionGuessResponse,
    SessionNextQuestionResponse,
    SessionEndResponse
)
from app.services.session_service import SessionService
from app.dependencies import get_session_service

router = APIRouter(prefix="/session", tags=["session"])


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
        request: Contains difficulty level
        
    Returns:
        Session ID, first question, and initial score
        
    Raises:
        HTTPException: 400 if invalid difficulty
    """
    try:
        result = session_service.create_session(request.difficulty, request.top_n)
        return SessionStartResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating session: {str(e)}"
        )


@router.post("/{session_id}/guess", response_model=SessionGuessResponse)
def submit_guess(
    session_id: str,
    request: SessionGuessRequest,
    session_service: SessionService = Depends(get_session_service)
):
    """
    Submit a guess for the current question in session
    
    Validates that guess is for the current question in the session,
    preventing cheating by guessing for different players.
    
    Args:
        session_id: Session identifier
        request: Contains player name guess
        
    Returns:
        Result with correctness, answer, score, and similarity
        
    Raises:
        HTTPException: 404 if session not found, 400 if no active question
    """
    try:
        result = session_service.submit_guess(session_id, request.guess)
        return SessionGuessResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting guess: {str(e)}"
        )


@router.post("/{session_id}/next", response_model=SessionNextQuestionResponse)
def get_next_question(
    session_id: str,
    request: SessionStartRequest,
    session_service: SessionService = Depends(get_session_service)
):
    """
    Get the next question in the session
    
    Call this after a guess to move to the next question.
    Question difficulty matches the session difficulty.
    
    Args:
        session_id: Session identifier
        
    Returns:
        New question with current session score
        
    Raises:
        HTTPException: 404 if session not found
    """
    try:
        result = session_service.get_next_question(session_id, request.difficulty, request.top_n)
        return SessionNextQuestionResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting next question: {str(e)}"
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
        session_id: Session identifier
        
    Returns:
        Final session statistics
        
    Raises:
        HTTPException: 404 if session not found
    """
    try:
        result = session_service.end_session(session_id)
        return SessionEndResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ending session: {str(e)}"
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
        session_id: Session identifier
        
    Returns:
        Current session data
        
    Raises:
        HTTPException: 404 if session not found
    """
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
        raise HTTPException(
            status_code=500,
            detail=f"Error getting session status: {str(e)}"
        )