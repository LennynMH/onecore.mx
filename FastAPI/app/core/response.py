"""Standardized response models."""

from typing import Any, Optional
from pydantic import BaseModel


class StandardResponse(BaseModel):
    """Standard API response model."""
    
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[list] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {},
                "errors": None
            }
        }

