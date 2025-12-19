"""Document domain entities."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any


@dataclass
class Document:
    """Document entity."""
    
    id: Optional[int] = None
    filename: str = ""
    original_filename: str = ""
    file_type: str = ""  # PDF, JPG, PNG
    s3_key: Optional[str] = None
    s3_bucket: Optional[str] = None
    classification: Optional[str] = None  # FACTURA, INFORMACIÓN
    uploaded_by: int = 0
    uploaded_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    file_size: Optional[int] = None
    extracted_data: Optional[Dict[str, Any]] = None


@dataclass
class Event:
    """Event entity for history module."""
    
    id: Optional[int] = None
    event_type: str = ""  # DOCUMENT_UPLOAD, AI_PROCESSING, USER_INTERACTION
    description: str = ""
    document_id: Optional[int] = None
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None

