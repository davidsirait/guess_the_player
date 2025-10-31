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
    similarity_score: int = Field(ge=0, le=100)
    all_possible_answers: List[str]


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