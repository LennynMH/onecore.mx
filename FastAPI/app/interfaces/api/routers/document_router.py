"""Document upload router."""

from fastapi import APIRouter, Depends, UploadFile, File, Query
from typing import Optional
from app.interfaces.schemas.document_schema import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentsListResponse
)
from app.interfaces.dependencies.auth_dependencies import require_role
from app.interfaces.api.controllers.document_controller import DocumentController
from app.application.use_cases.document_upload_use_cases import DocumentUploadUseCases
from app.infrastructure.s3.s3_service import S3Service
from app.infrastructure.ai.textract_service import TextractService
from app.infrastructure.ai.openai_service import OpenAIService
from app.infrastructure.repositories.document_repository import DocumentRepositoryImpl

router = APIRouter(tags=["Documents"])


def get_document_controller() -> DocumentController:
    """Dependency to get document upload controller."""
    s3_service = S3Service()
    textract_service = TextractService()
    openai_service = OpenAIService()
    # DocumentRepositoryImpl ahora usa SQLAlchemy y no requiere SQLServerService
    document_repository = DocumentRepositoryImpl()
    document_upload_use_case = DocumentUploadUseCases(
        s3_service, document_repository, textract_service, openai_service
    )
    return DocumentController(document_upload_use_case)


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role()),
    controller: DocumentController = Depends(get_document_controller)
):
    """Upload document (PDF, JPG, PNG) for analysis."""
    user_id = current_user.get("id_usuario")
    return await controller.upload_document(file, user_id)


@router.get("/documents", response_model=DocumentsListResponse)
async def list_documents(
    classification: Optional[str] = Query(None, description="Filter by classification (FACTURA, INFORMACIÓN)"),
    date_from: Optional[str] = Query(None, description="Filter by date from (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by date to (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(require_role()),
    controller: DocumentController = Depends(get_document_controller)
):
    """List documents with filters and pagination."""
    user_id = current_user.get("id_usuario")
    return await controller.list_documents(user_id, classification, date_from, date_to, page, limit)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: dict = Depends(require_role()),
    controller: DocumentController = Depends(get_document_controller)
):
    """Get document by ID."""
    return await controller.get_document(document_id)
