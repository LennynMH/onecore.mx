"""Authentication schemas."""

from pydantic import BaseModel
from typing import Optional


class LoginRequest(BaseModel):
    """Login request schema."""
    
    rol: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "rol": "admin"
            }
        }


class LoginResponse(BaseModel):
    """Login response schema."""
    
    access_token: str
    token_type: str
    expires_in: int
    user: dict

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
                "user": {
                    "id_usuario": 1,
                    "rol": "gestor"
                }
            }
        }


class TokenRenewalResponse(BaseModel):
    """Token renewal response schema."""
    
    access_token: str
    token_type: str
    expires_in: int
    user: dict

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id_usuario": 999,
                    "rol": "user"
                }
            }
        }


class TokenRenewalRequest(BaseModel):
    """Token renewal request schema."""
    
    token: str

    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }

