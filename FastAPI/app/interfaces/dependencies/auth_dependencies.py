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


def require_role(required_roles: str | list = None):
    """
    Dependency to require specific role(s).
    
    Args:
        required_roles: Required role(s) - can be:
            - String: "admin" or "admin,gestor" (comma-separated)
            - List: ["admin", "gestor"]
            - None: Uses FILE_UPLOAD_REQUIRED_ROLES from config
        
    Returns:
        Dependency function
    """
    # Determine which roles to check
    if required_roles is None:
        # Use configured roles from settings
        roles_to_check = settings.file_upload_required_roles_list
    elif isinstance(required_roles, str):
        # Parse comma-separated string
        roles_to_check = [
            role.strip().lower()
            for role in required_roles.split(",")
            if role.strip()
        ]
    elif isinstance(required_roles, list):
        # Use list directly
        roles_to_check = [role.lower() if isinstance(role, str) else str(role).lower() for role in required_roles]
    else:
        # Fallback to default
        roles_to_check = settings.file_upload_required_roles_list
    
    def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_role = user.get("rol", "").lower()
        if user_role not in roles_to_check:
            roles_str = ", ".join(roles_to_check)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role(s): {roles_str}, but user has role: {user.get('rol', 'unknown')}"
            )
        return user
    
    return role_checker

