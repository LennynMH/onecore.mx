"""Document repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.domain.entities.document import Document, Event


class DocumentRepository(ABC):
    """Abstract document repository."""
    
    @abstractmethod
    async def save_document(self, document: Document) -> Document:
        """Save document to database."""
        pass
    
    @abstractmethod
    async def get_document(self, document_id: int) -> Optional[Document]:
        """Get document by ID."""
        pass
    
    @abstractmethod
    async def list_documents(
        self,
        user_id: Optional[int] = None,
        classification: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        List documents with filters and pagination.
        
        Returns:
            Dictionary with 'total', 'page', 'limit', 'documents'
        """
        pass
    
    @abstractmethod
    async def save_extracted_data(
        self,
        document_id: int,
        data_type: str,
        extracted_data: Dict[str, Any]
    ) -> bool:
        """Save extracted data for a document."""
        pass
    
    @abstractmethod
    async def save_event(self, event: Event) -> Event:
        """Save event to database."""
        pass

