"""File repository interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.domain.entities.file_upload import FileUpload


class FileRepository(ABC):
    """Abstract file repository."""
    
    @abstractmethod
    async def save_file_data(self, file_data: List[Dict[str, Any]], metadata: FileUpload) -> bool:
        """Save file data to database."""
        pass
    
    @abstractmethod
    async def get_file_metadata(self, file_id: int) -> FileUpload:
        """Get file metadata by ID."""
        pass

