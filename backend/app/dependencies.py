"""
FastAPI dependencies for dependency injection
"""

from functools import lru_cache

from app.services.storage_interface import SessionStorage
from app.services.in_memory_storage import InMemoryStorage
from app.services.session_service import SessionService


# Storage instance (singleton)
_storage_instance: SessionStorage = None


def get_storage() -> SessionStorage:
    """
    Get storage instance (singleton)
    
    To switch to Redis later, change this to:
        return RedisStorage(redis_url)
    """
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = InMemoryStorage()
    return _storage_instance


def get_session_service() -> SessionService:
    """
    Get session service instance
    
    This is the dependency that will be injected into routes
    """
    storage = get_storage()
    return SessionService(storage)