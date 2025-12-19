"""Authentication controller."""

from fastapi import HTTPException, Request, status
from typing import Optional, Dict, Any
from app.application.use_cases.auth_use_cases import AuthUseCases
from app.interfaces.schemas.auth_schema import LoginRequest, LoginResponse, TokenRenewalResponse
from app.core.security import decode_token


class AuthController:
    """
    Controlador para operaciones de autenticación.
    
    ¿Qué hace la clase?
    Maneja la lógica de autenticación, incluyendo login de usuarios anónimos
    y renovación de tokens JWT.
    
    ¿Qué métodos tiene?
    - login: Inicia sesión de usuario anónimo y genera token JWT
    - renew_token: Renueva un token JWT existente
    """
    
    def __init__(self, auth_use_case: AuthUseCases):
        """
        Inicializa el controlador con el caso de uso de autenticación.
        
        ¿Qué parámetros recibe y de qué tipo?
        - auth_use_case (AuthUseCases): Instancia del caso de uso de autenticación
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
        self.auth_use_case = auth_use_case
    
    async def login(self, request: Optional[LoginRequest] = None) -> LoginResponse:
        """
        Endpoint de login para usuarios anónimos.
        
        ¿Qué hace la función?
        Crea o obtiene una sesión anónima de la base de datos y retorna un token JWT
        con información del usuario (id_usuario, rol) y tiempo de expiración de 15 minutos.
        
        ¿Qué parámetros recibe y de qué tipo?
        - request (LoginRequest | None): Cuerpo de la petición opcional con campo 'rol'
          - Si 'rol' es proporcionado, usa ese rol
          - Si 'rol' no es proporcionado, usa 'gestor' por defecto
        
        ¿Qué dato regresa y de qué tipo?
        - LoginResponse: Token JWT con información del usuario
        
        Raises:
            HTTPException: Si hay un error en el proceso de autenticación
        """
        # Get role from request body, default to None (which will become "gestor")
        rol = request.rol if request and request.rol else None
        
        result = await self.auth_use_case.login_anonymous_user(rol=rol)
        return LoginResponse(**result)
    
    async def renew_token(self, request: Request) -> TokenRenewalResponse:
        """
        Renueva un token JWT.
        
        ¿Qué hace la función?
        Genera un nuevo token con tiempo de expiración adicional.
        Solo funciona si el token original aún no ha expirado.
        
        ¿Qué parámetros recibe y de qué tipo?
        - request (Request): Objeto de petición FastAPI que contiene los headers
        
        ¿Qué dato regresa y de qué tipo?
        - TokenRenewalResponse: Nuevo token JWT con información del usuario
        
        Raises:
            HTTPException: Si falta el header Authorization, el token es inválido o ha expirado
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
        result = await AuthUseCases.renew_token(token)
        return TokenRenewalResponse(**result)

