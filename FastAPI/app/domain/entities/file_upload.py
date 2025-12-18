"""File upload entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class FileUpload:
    """File upload entity."""
    
    id: Optional[int] = None
    filename: Optional[str] = None
    s3_key: Optional[str] = None
    s3_bucket: Optional[str] = None
    uploaded_by: Optional[int] = None
    uploaded_at: Optional[datetime] = None
    validation_errors: Optional[List[dict]] = None
    row_count: Optional[int] = None

