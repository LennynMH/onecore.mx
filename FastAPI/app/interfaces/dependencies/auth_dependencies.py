"""Authentication dependencies."""

from fastapi import Depends, HTTPException, status, Request
from app.core.config import settings
from app.core.security import decode_token


def get_current_user(request: Request) -> dict:
    """
    Get current user from JWT token.
    
    Args:
        request: FastAPI request object
        
    Returns:
        User payload from token
        
    Raises:
        HTTPException: If user is not authenticated
    """
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return request.state.user


def require_role(required_role: str = None):
    """
    Dependency to require specific role.
    
    Args:
        required_role: Required role (defaults to FILE_UPLOAD_REQUIRED_ROLE from config)
        
    Returns:
        Dependency function
    """
    if required_role is None:
        required_role = settings.file_upload_required_role
    
    def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_role = user.get("rol")
        if user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}, but user has role: {user_role}"
            )
        return user
    
    return role_checker

