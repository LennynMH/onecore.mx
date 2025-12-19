"""API routers."""

from fastapi import APIRouter
from .auth_router import router as auth_router
from .file_router import router as file_router
from .document_router import router as document_router
from .history_router import router as history_router

def create_api_router() -> APIRouter:
    """Create main API router with all sub-routers."""
    api_router = APIRouter(prefix="/api/v1")
    
    # Include all routers
    api_router.include_router(auth_router, tags=["Authentication"])
    api_router.include_router(file_router, tags=["File Upload"])
    api_router.include_router(document_router, tags=["Documents"])
    api_router.include_router(history_router, tags=["History"])
    
    return api_router

