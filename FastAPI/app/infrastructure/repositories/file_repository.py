"""File repository implementation."""

from typing import List, Dict, Any
from app.domain.entities.file_upload import FileUpload
from app.domain.repositories.file_repository import FileRepository
from app.infrastructure.database.sql_server import SQLServerService


class FileRepositoryImpl(FileRepository):
    """File repository implementation."""
    
    def __init__(self, db_service: SQLServerService):
        """Initialize repository with database service."""
        self.db_service = db_service
    
    async def save_file_data(
        self,
        file_data: List[Dict[str, Any]],
        metadata: FileUpload
    ) -> bool:
        """Save file data to database."""
        return await self.db_service.save_file_data(file_data, metadata)
    
    async def get_file_metadata(self, file_id: int) -> FileUpload:
        """Get file metadata by ID."""
        return await self.db_service.get_file_metadata(file_id)

