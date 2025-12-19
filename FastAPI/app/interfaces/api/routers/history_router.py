"""History router."""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import datetime
from fastapi.responses import StreamingResponse
from app.interfaces.schemas.history_schema import HistoryResponse
from app.interfaces.dependencies.auth_dependencies import get_current_user
from app.interfaces.api.controllers.history_controller import HistoryController
from app.application.use_cases.history_use_cases import HistoryUseCases
from app.infrastructure.repositories.document_repository import DocumentRepositoryImpl

router = APIRouter(tags=["History"])


def get_history_controller() -> HistoryController:
    """Dependency to get history controller."""
    # DocumentRepositoryImpl ahora usa SQLAlchemy y no requiere SQLServerService
    document_repository = DocumentRepositoryImpl()
    history_use_case = HistoryUseCases(document_repository)
    return HistoryController(history_use_case)


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    document_id: Optional[int] = Query(None, description="Filter by document ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    classification: Optional[str] = Query(None, description="Filter by document classification"),
    date_from: Optional[datetime] = Query(None, description="Filter events from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter events to this date"),
    description_search: Optional[str] = Query(None, description="Search in event description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
    controller: HistoryController = Depends(get_history_controller)
):
    """Get history of events with filters and pagination."""
    return await controller.get_history(
        event_type, document_id, user_id, classification,
        date_from, date_to, description_search, page, page_size
    )


@router.get("/history/export", response_class=StreamingResponse)
async def export_history(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    document_id: Optional[int] = Query(None, description="Filter by document ID"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    classification: Optional[str] = Query(None, description="Filter by document classification"),
    date_from: Optional[datetime] = Query(None, description="Filter events from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter events to this date"),
    description_search: Optional[str] = Query(None, description="Search in event description"),
    include_document_details: bool = Query(True, description="Include document details in export"),
    current_user: dict = Depends(get_current_user),
    controller: HistoryController = Depends(get_history_controller)
):
    """Export history to Excel file."""
    return await controller.export_history(
        event_type, document_id, user_id, classification,
        date_from, date_to, description_search, include_document_details
    )
