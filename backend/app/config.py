"""
Configuration management for the Career Sequence Game API
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import json


class Settings(BaseSettings):
    """Application settings"""
    
    # App info
    app_name: str = "Guess the Player API"
    app_version: str = "1.0.0"
    
    # Database
    database_path: str = "transfermarkt.db"
    
    # CORS - will parse JSON string or comma-separated values
    cors_origins: str = "*"
    
    # Fuzzy matching threshold
    fuzzy_match_threshold: int = 85
    player_lookup_threshold: int = 70
    
    # Session settings
    session_ttl: int = 21600  # 6 hours (increased from 1 hour)
    session_cleanup_interval: int = 300
    
    # Redis url settings
    redis_url: str = "redis://localhost:6379"
    
    # Set limit based on market value for players retrieval
    top_players_limit: int = 100

    # set environment
    environment: str = "dev"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from string to list"""
        if self.cors_origins == "*":
            return ["*"]
        
        # Try to parse as JSON first
        try:
            origins = json.loads(self.cors_origins)
            if isinstance(origins, list):
                return origins
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Fall back to comma-separated
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()