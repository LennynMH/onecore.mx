"""File upload schemas."""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ValidationError(BaseModel):
    """Validation error schema."""
    
    type: str
    field: Optional[str] = None
    message: str
    row: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "type": "empty_value",
                "field": "email",
                "message": "Empty value in field 'email'",
                "row": 5
            }
        }


class FileUploadResponse(BaseModel):
    """File upload response schema."""
    
    success: bool
    message: str
    filename: str  # Unique filename with timestamp
    original_filename: Optional[str] = None  # Original filename from upload
    s3_key: Optional[str] = None
    s3_bucket: Optional[str] = None
    rows_processed: int
    validation_errors: List[ValidationError]
    param1: str
    param2: str

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "File uploaded successfully",
                "filename": "data.csv",
                "s3_key": "uploads/2024/01/15/data.csv",
                "s3_bucket": "bucket-name",
                "rows_processed": 100,
                "validation_errors": [],
                "param1": "value1",
                "param2": "value2"
            }
        }

