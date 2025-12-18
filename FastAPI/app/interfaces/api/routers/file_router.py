"""File upload router."""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from app.interfaces.schemas.file_schema import FileUploadResponse
from app.interfaces.dependencies.auth_dependencies import get_current_user, require_role
from app.application.use_cases.file_upload_use_cases import FileUploadUseCases
from app.infrastructure.s3.s3_service import S3Service
from app.infrastructure.repositories.file_repository import FileRepositoryImpl
from app.infrastructure.database.sql_server import SQLServerService

router = APIRouter(prefix="/files", tags=["File Upload"])


def get_file_upload_use_case() -> FileUploadUseCases:
    """Dependency to get file upload use case."""
    s3_service = S3Service()
    db_service = SQLServerService()
    file_repository = FileRepositoryImpl(db_service)
    return FileUploadUseCases(s3_service, file_repository)


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    param1: str = Form(...),
    param2: str = Form(...),
    current_user: dict = Depends(require_role()),
    use_case: FileUploadUseCases = Depends(get_file_upload_use_case)
):
    """
    Upload CSV file with validation.
    
    Requirements:
    - File is uploaded to AWS S3
    - File content is processed and saved to SQL Server
    - Returns validation errors (empty values, incorrect types, duplicates)
    - Access is limited to users with specific role (validated via JWT)
    
    Args:
        file: CSV file to upload
        param1: First additional parameter
        param2: Second additional parameter
        current_user: Current authenticated user (from JWT)
        use_case: File upload use case
        
    Returns:
        Upload result with validation errors
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )
    
    user_id = current_user.get("id_usuario")
    
    try:
        result = await use_case.upload_and_validate_file(
            file=file,
            param1=param1,
            param2=param2,
            user_id=user_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

