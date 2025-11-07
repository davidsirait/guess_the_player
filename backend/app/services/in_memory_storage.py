"""
In-memory implementation of session storage
Simple dictionary-based storage for development/MVP
"""

import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import fnmatch

from app.services.storage_interface import SessionStorage


class InMemoryStorage(SessionStorage):
    """
    In-memory session storage using Python dictionaries
    
    Note: Data is lost on restart. For production, use Redis.
    """
    
    def __init__(self):
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._expiry: Dict[str, float] = {}
    
    def set(self, key: str, value: Dict[str, Any], ttl: int) -> bool:
        """Store a value with expiration time"""
        self._storage[key] = value.copy()  # Store a copy to prevent mutations
        self._expiry[key] = time.time() + ttl
        return True
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a value, checking expiration"""
        # Check if key exists
        if key not in self._storage:
            return None
        
        # Check if expired
        if time.time() > self._expiry.get(key, 0):
            self.delete(key)
            return None
        
        return self._storage[key].copy()  # Return a copy to prevent mutations
    
    def delete(self, key: str) -> bool:
        """Delete a key-value pair"""
        existed = key in self._storage
        self._storage.pop(key, None)
        self._expiry.pop(key, None)
        return existed
    
    def exists(self, key: str) -> bool:
        """Check if key exists and not expired"""
        if key not in self._storage:
            return False
        
        # Check expiration
        if time.time() > self._expiry.get(key, 0):
            self.delete(key)
            return False
        
        return True
    
    def update(self, key: str, value: Dict[str, Any]) -> bool:
        """Update value while preserving TTL"""
        if not self.exists(key):
            return False
        
        # Update value, keep existing expiry
        self._storage[key] = value.copy()
        return True
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, expiry_time in self._expiry.items()
            if current_time > expiry_time
        ]
        
        for key in expired_keys:
            self.delete(key)
        
        return len(expired_keys)
    
    def get_all_keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching pattern"""
        # Clean up expired keys first
        self.cleanup_expired()
        
        if pattern == "*":
            return list(self._storage.keys())
        
        # Use fnmatch for pattern matching
        return [key for key in self._storage.keys() if fnmatch.fnmatch(key, pattern)]
    
    def get_stats(self) -> Dict[str, int]:
        """Get storage statistics (useful for monitoring)"""
        self.cleanup_expired()
        return {
            "total_keys": len(self._storage),
            "total_size_bytes": sum(
                len(str(v)) for v in self._storage.values()
            )
        }