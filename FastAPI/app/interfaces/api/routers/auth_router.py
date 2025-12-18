"""Authentication router."""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional
from app.application.use_cases.auth_use_cases import AuthUseCases
from app.interfaces.schemas.auth_schema import LoginRequest, LoginResponse, TokenRenewalResponse, TokenRenewalRequest
from app.core.security import decode_token
from app.infrastructure.repositories.auth_repository import AuthRepositoryImpl
from app.infrastructure.database.sql_server import SQLServerService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_use_case() -> AuthUseCases:
    """Dependency to get authentication use case."""
    db_service = SQLServerService()
    auth_repository = AuthRepositoryImpl(db_service)
    return AuthUseCases(auth_repository=auth_repository)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Optional[LoginRequest] = None,
    use_case: AuthUseCases = Depends(get_auth_use_case)
):
    """
    Login endpoint for anonymous users.
    
    Creates or gets an anonymous session from database and returns a JWT token
    with user information (id_usuario, rol) and 15 minutes expiration time.
    
    Args:
        request: Optional request body with 'rol' field
                 - If 'rol' is provided, uses that role
                 - If 'rol' is not provided, defaults to 'gestor'
    
    Returns:
        JWT token with user information
    """
    # Get role from request body, default to None (which will become "gestor")
    rol = request.rol if request and request.rol else None
    
    result = await use_case.login_anonymous_user(rol=rol)
    return result


@router.post("/renew", response_model=TokenRenewalResponse)
async def renew_token(request: Request):
    """
    Renew JWT token.
    
    Generates a new token with additional expiration time.
    Only works if the original token has not expired.
    """
    # Get token from Authorization header
    authorization = request.headers.get("Authorization") or request.headers.get("authorization")
    
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme"
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format"
        )
    
    # Validate token is not expired
    try:
        decode_token(token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Cannot renew expired token."
        )
    
    # Renew token
    # Note: renew_token is static and doesn't need repository
    result = await AuthUseCases.renew_token(token)
    return result

