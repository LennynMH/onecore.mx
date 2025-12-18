"""Authentication repository interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AuthRepository(ABC):
    """Repository interface for authentication operations."""
    
    @abstractmethod
    async def create_or_get_anonymous_session(self, rol: str = "admin") -> Dict[str, Any]:
        """
        Create a new anonymous session or get an existing one.
        
        Args:
            rol: Role to assign to the session
            
        Returns:
            Dictionary with session data (id, session_id, rol, created_at)
        """
        pass
    
    @abstractmethod
    async def update_session_activity(self, session_id: int) -> bool:
        """
        Update last activity timestamp for a session.
        
        Args:
            session_id: Session ID to update
            
        Returns:
            True if successful
        """
        pass

