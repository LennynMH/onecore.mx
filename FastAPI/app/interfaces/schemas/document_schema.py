"""Document schemas."""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """Response schema for document upload."""
    
    success: bool
    message: str
    document_id: Optional[int] = None  # Optional for compatibility
    filename: str
    original_filename: Optional[str] = None  # For compatibility
    s3_key: Optional[str] = None
    s3_bucket: Optional[str] = None
    classification: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None  # Will be populated when IA is implemented
    processing_time_ms: Optional[int] = None  # For future use
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Document uploaded successfully",
                "document_id": 1,
                "filename": "invoice_18122025201153.pdf",
                "original_filename": "invoice.pdf",
                "s3_key": "documents/2025/12/18/invoice_18122025201153.pdf",
                "s3_bucket": "onecore-uploads-dev",
                "classification": None
            }
        }


class DocumentResponse(BaseModel):
    """Response schema for a single document."""
    
    id: int
    filename: str
    original_filename: str
    file_type: str
    classification: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    extracted_data: Optional[Dict[str, Any]] = None
    s3_key: Optional[str] = None
    s3_bucket: Optional[str] = None
    file_size: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "filename": "invoice_18122025201153.pdf",
                "original_filename": "invoice.pdf",
                "file_type": "PDF",
                "classification": "FACTURA",
                "uploaded_at": "2025-12-18T20:11:53",
                "processed_at": "2025-12-18T20:12:05",
                "extracted_data": {
                    "client": {"name": "John Doe", "address": "123 Main St"},
                    "provider": {"name": "ACME Corp", "address": "456 Business Ave"},
                    "invoice_number": "INV-2025-001",
                    "date": "2025-12-18",
                    "total": 1500.00
                },
                "s3_key": "documents/2025/12/18/invoice_18122025201153.pdf",
                "s3_bucket": "onecore-uploads-dev",
                "file_size": 245760
            }
        }


class DocumentsListResponse(BaseModel):
    """Response schema for documents list."""
    
    total: int
    page: int
    limit: int
    documents: List[DocumentResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 50,
                "page": 1,
                "limit": 20,
                "documents": [
                    {
                        "id": 1,
                        "filename": "invoice_18122025201153.pdf",
                        "original_filename": "invoice.pdf",
                        "file_type": "PDF",
                        "classification": "FACTURA",
                        "uploaded_at": "2025-12-18T20:11:53",
                        "processed_at": "2025-12-18T20:12:05",
                        "extracted_data": None,
                        "s3_key": "documents/2025/12/18/invoice_18122025201153.pdf",
                        "s3_bucket": "onecore-uploads-dev",
                        "file_size": 245760
                    }
                ]
            }
        }

