"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import List


class Club(BaseModel):
    """Club information in a player's career sequence"""
    club: str
    logo: str
    season: str


class Question(BaseModel):
    """Question data for the guessing game"""
    player_id: str
    difficulty: str
    num_moves: int
    shared_by: int = Field(description="Number of players with same sequence")
    clubs: List[Club]


class GuessRequest(BaseModel):
    """Request to check a player guess"""
    player_id: str
    guess: str = Field(min_length=1, description="Player name guess")


class GuessResponse(BaseModel):
    """Response for a guess check"""
    correct: bool
    actual_answer: str
    actual_answer_img_url: str
    similarity_score: float = Field(ge=0, le=100)
    all_possible_answers: List[str]
    all_possible_answers_img_urls: List[str]


class PlayerLookupResponse(BaseModel):
    """Response for player lookup by name"""
    player_id: str
    player_name: str
    num_moves: int
    clubs: List[Club]


class DifficultyStats(BaseModel):
    """Statistics for a difficulty level"""
    difficulty: str
    count: int
    avg_moves: float
    min_moves: int
    max_moves: int


class StatsResponse(BaseModel):
    """Overall game statistics"""
    total_questions: int
    by_difficulty: List[DifficultyStats]

# Session-related models
class SessionStartRequest(BaseModel):
    """Request to start a new game session"""
    difficulty: str = Field(pattern="^(short|moderate|long)$")
    top_n: int = Field(gt=0, le=5000, description="Top N players to select questions from")


class SessionStartResponse(BaseModel):
    """Response when starting a new session"""
    session_id: str
    question: Question
    score: int = 0
    total_attempts: int = 0


class SessionGuessRequest(BaseModel):
    """Request to submit a guess in a session"""
    guess: str = Field(min_length=1, description="Player name guess")


class SessionGuessResponse(BaseModel):
    """Response for a session guess"""
    correct: bool
    actual_answer: str
    actual_answer_img_url: str
    similarity_score: float = Field(ge=0, le=100)
    all_possible_answers: List[str]
    all_possible_answers_img_urls: List[str]
    session_score: int
    total_attempts: int


class SessionNextQuestionResponse(BaseModel):
    """Response when getting next question"""
    question: Question
    session_score: int
    total_attempts: int


class SessionEndResponse(BaseModel):
    """Response when ending a session"""
    session_id: str
    final_score: int
    total_attempts: int
    correct_guesses: int
    accuracy: float
    difficulty: str
    duration: str