"""
Configuration management for the Career Sequence Game API
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # App info
    app_name: str = "Guess the Player API"
    app_version: str = "1.0.0"
    
    # Database
    database_path: str = "transfermarkt.db"
    
    # CORS
    cors_origins: list = ["*"]  # In production, use specific origins
    
    # Fuzzy matching threshold
    fuzzy_match_threshold: int = 85
    player_lookup_threshold: int = 70
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# cached the settings instance
@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()