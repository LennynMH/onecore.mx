"""Authentication router."""

from fastapi import APIRouter, Depends, Request
from typing import Optional
from app.interfaces.schemas.auth_schema import LoginRequest, LoginResponse, TokenRenewalResponse
from app.interfaces.api.controllers.auth_controller import AuthController
from app.application.use_cases.auth_use_cases import AuthUseCases
from app.infrastructure.repositories.auth_repository import AuthRepositoryImpl
from app.infrastructure.database.sql_server import SQLServerService

router = APIRouter(tags=["Authentication"])


def get_auth_controller() -> AuthController:
    """Dependency to get authentication controller."""
    db_service = SQLServerService()
    auth_repository = AuthRepositoryImpl(db_service)
    auth_use_case = AuthUseCases(auth_repository=auth_repository)
    return AuthController(auth_use_case)


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    request: Optional[LoginRequest] = None,
    controller: AuthController = Depends(get_auth_controller)
):
    """Login endpoint for anonymous users."""
    return await controller.login(request)


@router.post("/auth/renew", response_model=TokenRenewalResponse)
async def renew_token(
    request: Request,
    controller: AuthController = Depends(get_auth_controller)
):
    """Renew JWT token."""
    return await controller.renew_token(request)
