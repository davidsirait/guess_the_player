"""
Abstract storage interface for session management
Allows easy switching between in-memory, Redis, or other storage backends
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class SessionStorage(ABC):
    """Abstract base class for session storage implementations"""
    
    @abstractmethod
    def set(self, key: str, value: Dict[str, Any], ttl: int) -> bool:
        """
        Store a value with time-to-live
        
        Args:
            key: Storage key
            value: Data to store (must be JSON-serializable)
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a value by key
        
        Args:
            key: Storage key
            
        Returns:
            Stored value or None if not found/expired
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a value by key
        
        Args:
            key: Storage key
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if a key exists
        
        Args:
            key: Storage key
            
        Returns:
            True if key exists and not expired
        """
        pass
    
    @abstractmethod
    def update(self, key: str, value: Dict[str, Any]) -> bool:
        """
        Update an existing value (preserving TTL)
        
        Args:
            key: Storage key
            value: New data to store
            
        Returns:
            True if successful, False if key doesn't exist
        """
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """
        Remove expired entries
        
        Returns:
            Number of entries removed
        """
        pass
    
    @abstractmethod
    def get_all_keys(self, pattern: str = "*") -> List[str]:
        """
        Get all keys matching pattern
        
        Args:
            pattern: Key pattern (default: all keys)
            
        Returns:
            List of matching keys
        """
        pass