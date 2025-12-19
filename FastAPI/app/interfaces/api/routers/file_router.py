"""File upload router."""

from fastapi import APIRouter, Depends, UploadFile, File, Form
from app.interfaces.schemas.file_schema import FileUploadResponse
from app.interfaces.dependencies.auth_dependencies import require_role
from app.interfaces.api.controllers.file_controller import FileController
from app.application.use_cases.file_upload_use_cases import FileUploadUseCases
from app.infrastructure.s3.s3_service import S3Service
from app.infrastructure.repositories.file_repository import FileRepositoryImpl
from app.infrastructure.database.sql_server import SQLServerService

router = APIRouter(tags=["File Upload"])


def get_file_controller() -> FileController:
    """Dependency to get file upload controller."""
    s3_service = S3Service()
    db_service = SQLServerService()
    file_repository = FileRepositoryImpl(db_service)
    file_upload_use_case = FileUploadUseCases(s3_service, file_repository)
    return FileController(file_upload_use_case)


@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    param1: str = Form(...),
    param2: str = Form(...),
    current_user: dict = Depends(require_role()),
    controller: FileController = Depends(get_file_controller)
):
    """Upload CSV file with validation."""
    user_id = current_user.get("id_usuario")
    return await controller.upload_file(file, param1, param2, user_id)
