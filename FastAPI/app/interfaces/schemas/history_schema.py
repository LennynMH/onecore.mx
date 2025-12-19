"""History schemas for API requests and responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class HistoryFilter(BaseModel):
    """Filters for history query."""
    
    event_type: Optional[str] = Field(None, description="Filter by event type (DOCUMENT_UPLOAD, AI_PROCESSING, USER_INTERACTION)")
    document_id: Optional[int] = Field(None, description="Filter by document ID")
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    classification: Optional[str] = Field(None, description="Filter by document classification (FACTURA, INFORMACIÓN)")
    date_from: Optional[datetime] = Field(None, description="Filter events from this date")
    date_to: Optional[datetime] = Field(None, description="Filter events to this date")
    description_search: Optional[str] = Field(None, description="Search in event description")
    page: int = Field(1, ge=1, description="Page number for pagination")
    page_size: int = Field(50, ge=1, le=100, description="Number of items per page")


class EventResponse(BaseModel):
    """Event response model."""
    
    id: int
    event_type: str
    description: str
    document_id: Optional[int] = None
    document_filename: Optional[str] = None
    document_classification: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class HistoryResponse(BaseModel):
    """History response with pagination."""
    
    events: List[EventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class HistoryExportRequest(BaseModel):
    """Request for exporting history to Excel."""
    
    filters: Optional[HistoryFilter] = Field(None, description="Filters to apply to export")
    include_document_details: bool = Field(True, description="Include document details in export")

