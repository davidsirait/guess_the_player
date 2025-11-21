"""
Configuration management for the Career Sequence Game API
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
import json
import logging
import sys


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
    session_ttl: int = 21600  # 6 hours
    session_cleanup_interval: int = 300
    
    # Redis url settings
    redis_url: str = "redis://localhost:6379"
    
    # Set limit based on market value for players retrieval
    top_players_limit: int = 100

    # Set environment
    environment: str = "dev"
    
    # Logging level
    log_level: str = "INFO"
    
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
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() in ["production", "prod"]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


def setup_logging():
    """Configure application logging"""
    settings = get_settings()
    
    # Map string level to logging level
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    
    log_level = level_map.get(settings.log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # In production, also log to file
    if settings.is_production():
        try:
            file_handler = logging.FileHandler('app.log')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.warning(f"Could not create log file: {e}")
    
    return root_logger


# Initialize logging on module import
logger = setup_logging()