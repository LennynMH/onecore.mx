"""Authentication use cases."""

from datetime import timedelta
from typing import Dict, Any
from app.core.config import settings
from app.core.security import create_access_token, decode_token
from app.domain.repositories.auth_repository import AuthRepository


class AuthUseCases:
    """Authentication use cases."""
    
    def __init__(self, auth_repository: AuthRepository = None):
        """Initialize use cases with repository."""
        self.auth_repository = auth_repository
    
    async def login_anonymous_user(self, rol: str = None) -> Dict[str, Any]:
        """
        Login anonymous user and generate JWT token.
        
        Creates or gets an anonymous session from database and generates JWT token.
        
        Args:
            rol: Optional role name. If not provided, defaults to "gestor"
        
        Returns:
            Dictionary with token and user information
        """
        # Use provided role or default to "gestor"
        role_to_use = rol if rol else "gestor"
        
        # Get or create anonymous session from database
        if self.auth_repository:
            session_data = await self.auth_repository.create_or_get_anonymous_session(
                rol=role_to_use
            )
            user_data = {
                "id_usuario": session_data["id"],
                "rol": session_data["rol"]
            }
        else:
            # Fallback to hardcoded values if repository not provided
            # This should not happen in normal operation
            user_data = {
                "id_usuario": 999,  # Anonymous user ID (fallback)
                "rol": role_to_use
            }
        
        # Create token with 15 minutes expiration
        expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)
        token = create_access_token(data=user_data, expires_delta=expires_delta)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.jwt_expiration_minutes * 60,
            "user": user_data
        }
    
    @staticmethod
    async def renew_token(token: str) -> Dict[str, Any]:
        """
        Renew JWT token.
        
        Args:
            token: Current JWT token
            
        Returns:
            Dictionary with new token
        """
        # Decode current token to get user data
        payload = decode_token(token)
        
        # Extract user information
        user_data = {
            "id_usuario": payload.get("id_usuario"),
            "rol": payload.get("rol")
        }
        
        # Create new token with additional expiration time
        expires_delta = timedelta(minutes=settings.jwt_refresh_expiration_minutes)
        new_token = create_access_token(data=user_data, expires_delta=expires_delta)
        
        return {
            "access_token": new_token,
            "token_type": "bearer",
            "expires_in": settings.jwt_refresh_expiration_minutes * 60,
            "user": user_data
        }

