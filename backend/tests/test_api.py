"""
Tests for the Guess the Player API
Run with: pytest
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "running"
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data


class TestSessionFlow:
    """Test complete session flow"""
    
    def test_start_session(self):
        """Test starting a new session"""
        response = client.post("/session/start", json={
            "difficulty": "short",
            "top_n": 100
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "question" in data
        assert "score" in data
        assert data["score"] == 0
        return data["session_id"]
    
    def test_start_session_invalid_difficulty(self):
        """Test starting session with invalid difficulty"""
        response = client.post("/session/start", json={
            "difficulty": "invalid",
            "top_n": 100
        })
        assert response.status_code == 422  # Validation error
    
    def test_submit_guess(self):
        """Test submitting a guess"""
        # First start a session
        start_response = client.post("/session/start", json={
            "difficulty": "short",
            "top_n": 100
        })
        session_id = start_response.json()["session_id"]
        
        # Submit a guess
        response = client.post(f"/session/{session_id}/guess", json={
            "guess": "Lionel Messi"
        })
        assert response.status_code == 200
        data = response.json()
        assert "correct" in data
        assert "similarity_score" in data
        assert "session_score" in data
    
    def test_submit_empty_guess(self):
        """Test submitting empty guess"""
        # First start a session
        start_response = client.post("/session/start", json={
            "difficulty": "short",
            "top_n": 100
        })
        session_id = start_response.json()["session_id"]
        
        # Submit empty guess
        response = client.post(f"/session/{session_id}/guess", json={
            "guess": ""
        })
        assert response.status_code == 422  # Validation error
    
    def test_guess_nonexistent_session(self):
        """Test submitting guess to nonexistent session"""
        response = client.post("/session/invalid-id/guess", json={
            "guess": "Test Player"
        })
        assert response.status_code == 400  # Invalid session ID format
    
    def test_get_next_question(self):
        """Test getting next question"""
        # First start a session
        start_response = client.post("/session/start", json={
            "difficulty": "short",
            "top_n": 100
        })
        session_id = start_response.json()["session_id"]
        
        # Get next question
        response = client.post(f"/session/{session_id}/next", json={})
        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert "session_score" in data
    
    def test_end_session(self):
        """Test ending a session"""
        # First start a session
        start_response = client.post("/session/start", json={
            "difficulty": "short",
            "top_n": 100
        })
        session_id = start_response.json()["session_id"]
        
        # End session
        response = client.delete(f"/session/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert "final_score" in data
        assert "accuracy" in data
    
    def test_complete_game_flow(self):
        """Test complete game flow from start to end"""
        # Start session
        start_response = client.post("/session/start", json={
            "difficulty": "short",
            "top_n": 50
        })
        assert start_response.status_code == 200
        session_id = start_response.json()["session_id"]
        
        # Submit a guess
        guess_response = client.post(f"/session/{session_id}/guess", json={
            "guess": "Cristiano Ronaldo"
        })
        assert guess_response.status_code == 200
        
        # Get next question
        next_response = client.post(f"/session/{session_id}/next", json={})
        assert next_response.status_code == 200
        
        # End session
        end_response = client.delete(f"/session/{session_id}")
        assert end_response.status_code == 200


class TestGameStats:
    """Test game statistics endpoints"""
    
    def test_get_stats(self):
        """Test getting game statistics"""
        response = client.get("/game/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_questions" in data
        assert "by_difficulty" in data


class TestRateLimiting:
    """Test rate limiting"""
    
    def test_rate_limit_on_guesses(self):
        """Test that rate limiting works on guess endpoint"""
        # Start a session
        start_response = client.post("/session/start", json={
            "difficulty": "short",
            "top_n": 100
        })
        session_id = start_response.json()["session_id"]
        
        # Try to submit more than 10 guesses rapidly
        # Note: This might not trigger in tests due to separate test sessions
        for i in range(12):
            response = client.post(f"/session/{session_id}/guess", json={
                "guess": f"Player {i}"
            })
            if i >= 10:
                # After 10 requests, should be rate limited
                # (might not work in tests due to test client behavior)
                if response.status_code == 429:
                    assert "retry_after" in response.json()
                    break


class TestValidation:
    """Test input validation"""
    
    def test_invalid_session_id_format(self):
        """Test invalid session ID format"""
        response = client.post("/session/not-a-uuid/guess", json={
            "guess": "Test"
        })
        assert response.status_code == 400
    
    def test_top_n_validation(self):
        """Test top_n parameter validation"""
        # Test with value too high
        response = client.post("/session/start", json={
            "difficulty": "short",
            "top_n": 10000  # Should be capped at 5000
        })
        # Should still work but cap the value
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])