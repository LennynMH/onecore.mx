"""Document repository implementation."""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.domain.entities.document import Document, Event
from app.domain.repositories.document_repository import DocumentRepository
from app.infrastructure.database.sql_server import SQLServerService

logger = logging.getLogger(__name__)


class DocumentRepositoryImpl(DocumentRepository):
    """Document repository implementation."""
    
    def __init__(self, db_service: SQLServerService):
        """Initialize repository with database service."""
        self.db_service = db_service
    
    async def save_document(self, document: Document) -> Document:
        """Save document to database."""
        conn = None
        cursor = None
        try:
            conn = self.db_service.get_connection()
            cursor = conn.cursor()
            
            if document.id:
                # Update existing document
                cursor.execute("""
                    UPDATE documents
                    SET filename = ?, original_filename = ?, file_type = ?,
                        s3_key = ?, s3_bucket = ?, classification = ?,
                        processed_at = ?, file_size = ?
                    WHERE id = ?
                """, (
                    document.filename,
                    document.original_filename,
                    document.file_type,
                    document.s3_key,
                    document.s3_bucket,
                    document.classification,
                    document.processed_at,
                    document.file_size,
                    document.id
                ))
                conn.commit()
                return document
            else:
                # Insert new document
                cursor.execute("""
                    INSERT INTO documents (
                        filename, original_filename, file_type, s3_key, s3_bucket,
                        classification, uploaded_by, uploaded_at, processed_at, file_size
                    )
                    OUTPUT INSERTED.id, INSERTED.uploaded_at
                    VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), ?, ?)
                """, (
                    document.filename,
                    document.original_filename,
                    document.file_type,
                    document.s3_key,
                    document.s3_bucket,
                    document.classification,
                    document.uploaded_by,
                    document.processed_at,
                    document.file_size
                ))
                
                row = cursor.fetchone()
                if row:
                    document.id = row[0]
                    document.uploaded_at = row[1]
                
                conn.commit()
                return document
                
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            if conn:
                conn.rollback()
            raise Exception(f"Failed to save document: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    async def get_document(self, document_id: int) -> Optional[Document]:
        """Get document by ID."""
        conn = None
        cursor = None
        try:
            conn = self.db_service.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, filename, original_filename, file_type, s3_key, s3_bucket,
                       classification, uploaded_by, uploaded_at, processed_at, file_size
                FROM documents
                WHERE id = ?
            """, (document_id,))
            
            row = cursor.fetchone()
            if row:
                # Get extracted data if exists
                cursor.execute("""
                    SELECT data_type, extracted_data
                    FROM document_extracted_data
                    WHERE document_id = ?
                    ORDER BY created_at DESC
                """, (document_id,))
                
                extracted_data = None
                extracted_row = cursor.fetchone()
                if extracted_row:
                    extracted_data = json.loads(extracted_row[1])
                
                return Document(
                    id=row[0],
                    filename=row[1],
                    original_filename=row[2],
                    file_type=row[3],
                    s3_key=row[4],
                    s3_bucket=row[5],
                    classification=row[6],
                    uploaded_by=row[7],
                    uploaded_at=row[8],
                    processed_at=row[9],
                    file_size=row[10],
                    extracted_data=extracted_data
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            raise Exception(f"Failed to get document: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    async def list_documents(
        self,
        user_id: Optional[int] = None,
        classification: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """List documents with filters and pagination."""
        conn = None
        cursor = None
        try:
            conn = self.db_service.get_connection()
            cursor = conn.cursor()
            
            # Build WHERE clause
            conditions = []
            params = []
            
            if user_id:
                conditions.append("uploaded_by = ?")
                params.append(user_id)
            
            if classification:
                conditions.append("classification = ?")
                params.append(classification)
            
            if date_from:
                conditions.append("uploaded_at >= ?")
                params.append(date_from)
            
            if date_to:
                conditions.append("uploaded_at <= ?")
                params.append(date_to)
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            
            # Get total count
            cursor.execute(f"""
                SELECT COUNT(*) FROM documents WHERE {where_clause}
            """, params)
            total = cursor.fetchone()[0]
            
            # Get paginated results
            offset = (page - 1) * limit
            cursor.execute(f"""
                SELECT id, filename, original_filename, file_type, s3_key, s3_bucket,
                       classification, uploaded_by, uploaded_at, processed_at, file_size
                FROM documents
                WHERE {where_clause}
                ORDER BY uploaded_at DESC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, params + [offset, limit])
            
            documents = []
            for row in cursor.fetchall():
                documents.append(Document(
                    id=row[0],
                    filename=row[1],
                    original_filename=row[2],
                    file_type=row[3],
                    s3_key=row[4],
                    s3_bucket=row[5],
                    classification=row[6],
                    uploaded_by=row[7],
                    uploaded_at=row[8],
                    processed_at=row[9],
                    file_size=row[10]
                ))
            
            return {
                "total": total,
                "page": page,
                "limit": limit,
                "documents": documents
            }
            
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            raise Exception(f"Failed to list documents: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    async def save_extracted_data(
        self,
        document_id: int,
        data_type: str,
        extracted_data: Dict[str, Any]
    ) -> bool:
        """Save extracted data for a document."""
        conn = None
        cursor = None
        try:
            conn = self.db_service.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO document_extracted_data (document_id, data_type, extracted_data)
                VALUES (?, ?, ?)
            """, (
                document_id,
                data_type,
                json.dumps(extracted_data, ensure_ascii=False)
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving extracted data: {str(e)}")
            if conn:
                conn.rollback()
            raise Exception(f"Failed to save extracted data: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    async def save_event(self, event: Event) -> Event:
        """Save event to database."""
        conn = None
        cursor = None
        try:
            conn = self.db_service.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO events (event_type, description, document_id, user_id, created_at)
                OUTPUT INSERTED.id, INSERTED.created_at
                VALUES (?, ?, ?, ?, GETDATE())
            """, (
                event.event_type,
                event.description,
                event.document_id,
                event.user_id
            ))
            
            row = cursor.fetchone()
            if row:
                event.id = row[0]
                event.created_at = row[1]
            
            conn.commit()
            return event
            
        except Exception as e:
            logger.error(f"Error saving event: {str(e)}")
            if conn:
                conn.rollback()
            raise Exception(f"Failed to save event: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    async def list_events(
        self,
        event_type: Optional[str] = None,
        document_id: Optional[int] = None,
        user_id: Optional[int] = None,
        classification: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        description_search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """List events with filters and pagination."""
        conn = None
        cursor = None
        try:
            conn = self.db_service.get_connection()
            cursor = conn.cursor()
            
            # Build WHERE clause
            where_conditions = []
            params = []
            
            if event_type:
                where_conditions.append("e.event_type = ?")
                params.append(event_type)
            
            if document_id:
                where_conditions.append("e.document_id = ?")
                params.append(document_id)
            
            if user_id:
                where_conditions.append("e.user_id = ?")
                params.append(user_id)
            
            if classification:
                where_conditions.append("d.classification = ?")
                params.append(classification)
            
            if date_from:
                where_conditions.append("e.created_at >= ?")
                params.append(date_from)
            
            if date_to:
                where_conditions.append("e.created_at <= ?")
                params.append(date_to)
            
            if description_search:
                where_conditions.append("e.description LIKE ?")
                params.append(f"%{description_search}%")
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # Count total
            count_query = f"""
                SELECT COUNT(*)
                FROM events e
                LEFT JOIN documents d ON e.document_id = d.id
                WHERE {where_clause}
            """
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # Calculate pagination
            total_pages = (total + page_size - 1) // page_size
            offset = (page - 1) * page_size
            
            # Get events with document info
            query = f"""
                SELECT 
                    e.id,
                    e.event_type,
                    e.description,
                    e.document_id,
                    d.filename as document_filename,
                    d.classification as document_classification,
                    e.user_id,
                    e.created_at
                FROM events e
                LEFT JOIN documents d ON e.document_id = d.id
                WHERE {where_clause}
                ORDER BY e.created_at DESC
                OFFSET ? ROWS
                FETCH NEXT ? ROWS ONLY
            """
            
            params_with_pagination = params + [offset, page_size]
            cursor.execute(query, params_with_pagination)
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    "id": row[0],
                    "event_type": row[1],
                    "description": row[2],
                    "document_id": row[3],
                    "document_filename": row[4],
                    "document_classification": row[5],
                    "user_id": row[6],
                    "created_at": row[7]
                })
            
            return {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "events": events
            }
            
        except Exception as e:
            logger.error(f"Error listing events: {str(e)}")
            raise Exception(f"Failed to list events: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

