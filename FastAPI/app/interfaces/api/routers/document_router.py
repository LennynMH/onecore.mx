"""Document upload router."""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, status
from typing import Optional
from app.interfaces.schemas.document_schema import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentsListResponse
)
from app.interfaces.dependencies.auth_dependencies import require_role
from app.application.use_cases.document_upload_use_cases import DocumentUploadUseCases
from app.infrastructure.s3.s3_service import S3Service
from app.infrastructure.ai.textract_service import TextractService
from app.infrastructure.repositories.document_repository import DocumentRepositoryImpl
from app.infrastructure.database.sql_server import SQLServerService
from app.domain.entities.document import Document

router = APIRouter(prefix="/documents", tags=["Documents"])


def get_document_upload_use_case() -> DocumentUploadUseCases:
    """Dependency to get document upload use case."""
    s3_service = S3Service()
    textract_service = TextractService()
    db_service = SQLServerService()
    document_repository = DocumentRepositoryImpl(db_service)
    return DocumentUploadUseCases(s3_service, document_repository, textract_service)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_role()),
    use_case: DocumentUploadUseCases = Depends(get_document_upload_use_case)
):
    """
    Upload document (PDF, JPG, PNG) for analysis.
    
    Requirements:
    - File is uploaded to AWS S3
    - Document metadata is saved to SQL Server
    - Access is limited to users with specific role (validated via JWT)
    
    Args:
        file: Document file to upload (PDF, JPG, PNG)
        current_user: Current authenticated user (from JWT)
        use_case: Document upload use case
        
    Returns:
        Upload result with document information
    """
    # Validate file type
    valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
    file_extension = None
    if file.filename:
        file_extension = '.' + file.filename.split('.')[-1].lower()
    
    if not file_extension or file_extension not in valid_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a PDF, JPG, or PNG file"
        )
    
    user_id = current_user.get("id_usuario")
    
    try:
        result = await use_case.upload_document(
            file=file,
            user_id=user_id
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )


@router.get("", response_model=DocumentsListResponse)
async def list_documents(
    classification: Optional[str] = Query(None, description="Filter by classification (FACTURA, INFORMACIÓN)"),
    date_from: Optional[str] = Query(None, description="Filter by date from (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by date to (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(require_role()),
    use_case: DocumentUploadUseCases = Depends(get_document_upload_use_case)
):
    """
    List documents with filters and pagination.
    
    Args:
        classification: Filter by classification type
        date_from: Filter by start date
        date_to: Filter by end date
        page: Page number (starts at 1)
        limit: Items per page (max 100)
        current_user: Current authenticated user (from JWT)
        use_case: Document upload use case
        
    Returns:
        List of documents with pagination info
    """
    user_id = current_user.get("id_usuario")
    
    try:
        # Get repository from use case
        db_service = SQLServerService()
        document_repository = DocumentRepositoryImpl(db_service)
        
        result = await document_repository.list_documents(
            user_id=user_id,
            classification=classification,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit
        )
        
        # Convert Document entities to DocumentResponse
        documents_response = []
        for doc in result["documents"]:
            documents_response.append(DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                original_filename=doc.original_filename,
                file_type=doc.file_type,
                classification=doc.classification,
                uploaded_at=doc.uploaded_at,
                processed_at=doc.processed_at,
                extracted_data=doc.extracted_data,
                s3_key=doc.s3_key,
                s3_bucket=doc.s3_bucket,
                file_size=doc.file_size
            ))
        
        return DocumentsListResponse(
            total=result["total"],
            page=result["page"],
            limit=result["limit"],
            documents=documents_response
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    current_user: dict = Depends(require_role()),
    use_case: DocumentUploadUseCases = Depends(get_document_upload_use_case)
):
    """
    Get document by ID.
    
    Args:
        document_id: Document ID
        current_user: Current authenticated user (from JWT)
        use_case: Document upload use case
        
    Returns:
        Document information
    """
    try:
        # Get repository from use case
        db_service = SQLServerService()
        document_repository = DocumentRepositoryImpl(db_service)
        
        document = await document_repository.get_document(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            original_filename=document.original_filename,
            file_type=document.file_type,
            classification=document.classification,
            uploaded_at=document.uploaded_at,
            processed_at=document.processed_at,
            extracted_data=document.extracted_data,
            s3_key=document.s3_key,
            s3_bucket=document.s3_bucket,
            file_size=document.file_size
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting document: {str(e)}"
        )

