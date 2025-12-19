"""Health check router."""

from fastapi import APIRouter
from app.interfaces.api.controllers.health_controller import HealthController

router = APIRouter(tags=["Health"])

# Create controller instance
health_controller = HealthController()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return await health_controller.health_check()

