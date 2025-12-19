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
        Inicia sesión de usuario anónimo y genera token JWT.
        
        ¿Qué hace la función?
        Crea o obtiene una sesión anónima de la base de datos y genera un token JWT
        con los datos del usuario. Si no se proporciona un rol, usa "gestor" por defecto.
        
        ¿Qué parámetros recibe y de qué tipo?
        - rol (str | None): Nombre del rol del usuario. Opcional. Si es None, se usa "gestor".
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con las siguientes claves:
            - access_token (str): Token JWT generado
            - token_type (str): Tipo de token, siempre "bearer"
            - expires_in (int): Tiempo de expiración en segundos
            - user (Dict[str, Any]): Datos del usuario con id_usuario (int) y rol (str)
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
        Renueva un token JWT existente.
        
        ¿Qué hace la función?
        Decodifica el token JWT actual, extrae los datos del usuario y genera un nuevo
        token con tiempo de expiración adicional. Solo funciona si el token original
        aún no ha expirado.
        
        ¿Qué parámetros recibe y de qué tipo?
        - token (str): Token JWT actual que se desea renovar. Debe ser válido y no expirado.
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con las siguientes claves:
            - access_token (str): Nuevo token JWT generado
            - token_type (str): Tipo de token, siempre "bearer"
            - expires_in (int): Tiempo de expiración en segundos del nuevo token
            - user (Dict[str, Any]): Datos del usuario con id_usuario (int) y rol (str)
        
        Raises:
            Exception: Si el token es inválido o ha expirado.
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

