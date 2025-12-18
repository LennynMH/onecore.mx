"""User entity."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """User entity."""
    
    id_usuario: int
    rol: str
    email: Optional[str] = None

