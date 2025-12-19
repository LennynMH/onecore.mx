"""History router."""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime

from app.interfaces.schemas.history_schema import HistoryFilter, HistoryResponse, EventResponse, HistoryExportRequest
from app.interfaces.dependencies.auth_dependencies import get_current_user
from app.application.use_cases.history_use_cases import HistoryUseCases
from app.infrastructure.repositories.document_repository import DocumentRepositoryImpl
from app.infrastructure.database.sql_server import SQLServerService

router = APIRouter(prefix="/history", tags=["History"])


def get_history_use_case() -> HistoryUseCases:
    """Dependency to get history use case."""
    db_service = SQLServerService()
    document_repository = DocumentRepositoryImpl(db_service)
    return HistoryUseCases(document_repository)


@router.get("", response_model=HistoryResponse)
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
    use_case: HistoryUseCases = Depends(get_history_use_case)
):
    """
    Get history of events with filters and pagination.
    
    Filters:
    - event_type: DOCUMENT_UPLOAD, AI_PROCESSING, USER_INTERACTION
    - document_id: Filter by specific document
    - user_id: Filter by user
    - classification: FACTURA, INFORMACIÓN
    - date_from: Start date
    - date_to: End date
    - description_search: Search in description
    
    Returns:
        History with events and pagination info
    """
    try:
        result = await use_case.get_history(
            event_type=event_type,
            document_id=document_id,
            user_id=user_id,
            classification=classification,
            date_from=date_from,
            date_to=date_to,
            description_search=description_search,
            page=page,
            page_size=page_size
        )
        
        # Convert to response model
        events = [
            EventResponse(
                id=e["id"],
                event_type=e["event_type"],
                description=e["description"],
                document_id=e.get("document_id"),
                document_filename=e.get("document_filename"),
                document_classification=e.get("document_classification"),
                user_id=e.get("user_id"),
                created_at=e["created_at"]
            )
            for e in result["events"]
        ]
        
        return HistoryResponse(
            events=events,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting history: {str(e)}"
        )


@router.get("/export", response_class=StreamingResponse)
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
    use_case: HistoryUseCases = Depends(get_history_use_case)
):
    """
    Export history to Excel file.
    
    Uses the same filters as GET /history endpoint.
    
    Returns:
        Excel file (.xlsx) with history data
    """
    try:
        excel_buffer = await use_case.export_to_excel(
            event_type=event_type,
            document_id=document_id,
            user_id=user_id,
            classification=classification,
            date_from=date_from,
            date_to=date_to,
            description_search=description_search,
            include_document_details=include_document_details
        )
        
        from datetime import datetime
        filename = f"historial_eventos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            excel_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting history: {str(e)}"
        )

