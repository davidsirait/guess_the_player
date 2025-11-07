"""
Session management service for game sessions
Handles session lifecycle and game state
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import HTTPException

from app.services.storage_interface import SessionStorage
from app.services.game_service import GameService
from app.models.schemas import Question
from app.config import get_settings


class SessionService:
    """Service for managing game sessions"""
    
    def __init__(self, storage: SessionStorage):
        self.storage = storage
        self.game_service = GameService()
        self.settings = get_settings()
    
    def create_session(self, difficulty: str) -> Dict[str, Any]:
        """
        Create a new game session
        
        Args:
            difficulty: Game difficulty level
            
        Returns:
            Session data with first question
        """
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Get first question
        question = self.game_service.get_random_question(difficulty)
        
        # Create session data
        session_data = {
            "session_id": session_id,
            "difficulty": difficulty,
            "current_question_player_id": question.player_id,
            "score": 0,
            "total_attempts": 0,
            "correct_guesses": 0,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        # Store session with TTL (default 1 hour)
        ttl = getattr(self.settings, 'session_ttl', 3600)
        self.storage.set(f"session:{session_id}", session_data, ttl)
        
        return {
            "session_id": session_id,
            "question": question,
            "score": 0,
            "total_attempts": 0
        }
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get session data
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data
            
        Raises:
            HTTPException: If session not found or expired
        """
        session_data = self.storage.get(f"session:{session_id}")
        
        if not session_data:
            raise HTTPException(
                status_code=404,
                detail="Session not found or expired"
            )
        
        return session_data
    
    def submit_guess(self, session_id: str, guess: str) -> Dict[str, Any]:
        """
        Submit a guess for the current question in session
        
        Args:
            session_id: Session identifier
            guess: Player name guess
            
        Returns:
            Guess result with updated session info
        """
        # Get session
        session_data = self.get_session(session_id)
        
        # Get current question's player ID
        current_player_id = session_data.get("current_question_player_id")
        
        if not current_player_id:
            raise HTTPException(
                status_code=400,
                detail="No active question in session"
            )
        
        # Check guess
        guess_result = self.game_service.check_guess(current_player_id, guess)
        
        # Update session stats
        session_data["total_attempts"] += 1
        session_data["last_activity"] = datetime.now().isoformat()
        
        if guess_result.correct:
            session_data["score"] += 1
            session_data["correct_guesses"] += 1
        
        # Update session in storage
        self.storage.update(f"session:{session_id}", session_data)
        
        return {
            "correct": guess_result.correct,
            "actual_answer": guess_result.actual_answer,
            "similarity_score": guess_result.similarity_score,
            "all_possible_answers": guess_result.all_possible_answers,
            "session_score": session_data["score"],
            "total_attempts": session_data["total_attempts"]
        }
    
    def get_next_question(self, session_id: str) -> Dict[str, Any]:
        """
        Get next question for the session
        
        Args:
            session_id: Session identifier
            
        Returns:
            New question data
        """
        # Get session
        session_data = self.get_session(session_id)
        
        # Get new question with same difficulty
        difficulty = session_data.get("difficulty", "medium")
        question = self.game_service.get_random_question(difficulty)
        
        # Update session with new question
        session_data["current_question_player_id"] = question.player_id
        session_data["last_activity"] = datetime.now().isoformat()
        
        self.storage.update(f"session:{session_id}", session_data)
        
        return {
            "question": question,
            "session_score": session_data["score"],
            "total_attempts": session_data["total_attempts"]
        }
    
    def end_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a game session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Final session statistics
        """
        session_data = self.get_session(session_id)
        
        # Get final stats
        final_stats = {
            "session_id": session_id,
            "final_score": session_data["score"],
            "total_attempts": session_data["total_attempts"],
            "correct_guesses": session_data["correct_guesses"],
            "accuracy": (
                session_data["correct_guesses"] / session_data["total_attempts"] * 100
                if session_data["total_attempts"] > 0 else 0
            ),
            "difficulty": session_data["difficulty"],
            "duration": self._calculate_duration(session_data["created_at"])
        }
        
        # Delete session
        self.storage.delete(f"session:{session_id}")
        
        return final_stats
    
    def _calculate_duration(self, created_at_iso: str) -> str:
        """Calculate session duration in human-readable format"""
        try:
            created_at = datetime.fromisoformat(created_at_iso)
            duration = datetime.now() - created_at
            minutes = int(duration.total_seconds() / 60)
            seconds = int(duration.total_seconds() % 60)
            return f"{minutes}m {seconds}s"
        except:
            return "unknown"
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            Number of sessions cleaned up
        """
        return self.storage.cleanup_expired()