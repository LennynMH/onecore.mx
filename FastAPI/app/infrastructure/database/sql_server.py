"""SQL Server database service."""

import json
import logging
from typing import List, Dict, Any, Optional
import pyodbc
from datetime import datetime

from app.core.config import settings
from app.domain.entities.file_upload import FileUpload

logger = logging.getLogger(__name__)


class SQLServerService:
    """Service for SQL Server operations."""
    
    def __init__(self):
        """Initialize SQL Server connection."""
        self.connection_string = settings.sql_server_connection_string
    
    def get_connection(self):
        """Get database connection."""
        try:
            return pyodbc.connect(self.connection_string)
        except Exception as e:
            logger.error(f"Error connecting to SQL Server: {str(e)}")
            raise Exception(f"Failed to connect to SQL Server: {str(e)}")
    
    async def save_file_data(
        self,
        file_data: List[Dict[str, Any]],
        metadata: FileUpload
    ) -> bool:
        """
        Save file data to database.
        
        Args:
            file_data: List of dictionaries containing CSV row data
            metadata: File upload metadata
            
        Returns:
            True if successful
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create table if not exists
            self._create_file_data_table(cursor)
            
            # Determine if file has errors
            has_errors = 1 if metadata.validation_errors and len(metadata.validation_errors) > 0 else 0
            error_count = len(metadata.validation_errors) if metadata.validation_errors else 0
            
            # Insert file metadata (including has_errors and error_count)
            cursor.execute("""
                INSERT INTO file_uploads (filename, s3_key, s3_bucket, uploaded_by, uploaded_at, row_count, has_errors, error_count)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.filename,
                metadata.s3_key,
                metadata.s3_bucket,
                metadata.uploaded_by,
                datetime.utcnow(),
                len(file_data),
                has_errors,
                error_count
            ))
            
            file_id = cursor.fetchone()[0]
            
            # Insert file data rows
            if file_data:
                # Store each row as JSON for flexibility with different CSV structures
                for row in file_data:
                    row_json = json.dumps(row, ensure_ascii=False)
                    cursor.execute("""
                        INSERT INTO file_data (file_id, row_data)
                        VALUES (?, ?)
                    """, (file_id, row_json))
            
            # Insert validation errors if any
            if metadata.validation_errors and len(metadata.validation_errors) > 0:
                self._save_validation_errors(cursor, file_id, metadata.validation_errors)
            
            conn.commit()
            logger.info(f"File data saved to database. File ID: {file_id}, Rows: {len(file_data)}, Errors: {error_count}")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error saving file data: {str(e)}")
            raise Exception(f"Failed to save file data: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def _create_file_data_table(self, cursor):
        """Create file data table if not exists."""
        try:
            # Create file_uploads table
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'file_uploads')
                CREATE TABLE file_uploads (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    filename NVARCHAR(255) NOT NULL,
                    s3_key NVARCHAR(500),
                    s3_bucket NVARCHAR(255),
                    uploaded_by INT,
                    uploaded_at DATETIME2 NOT NULL,
                    row_count INT,
                    has_errors BIT DEFAULT 0,
                    error_count INT DEFAULT 0,
                    created_at DATETIME2 DEFAULT GETDATE()
                )
            """)
            
            # Create file_data table (generic structure with JSON column for flexibility)
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'file_data')
                CREATE TABLE file_data (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    file_id INT NOT NULL,
                    row_data NVARCHAR(MAX),  -- Store row data as JSON string
                    FOREIGN KEY (file_id) REFERENCES file_uploads(id) ON DELETE CASCADE,
                    created_at DATETIME2 DEFAULT GETDATE()
                )
            """)
            
        except Exception as e:
            logger.warning(f"Error creating tables (may already exist): {str(e)}")
    
    def _save_validation_errors(self, cursor, file_id: int, validation_errors: List[Dict[str, Any]]):
        """
        Save validation errors to database.
        
        Args:
            cursor: Database cursor
            file_id: File ID
            validation_errors: List of validation error dictionaries
        """
        try:
            for error in validation_errors:
                cursor.execute("""
                    INSERT INTO file_validation_errors (file_id, error_type, field_name, error_message, row_number)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    file_id,
                    error.get("type", "unknown"),
                    error.get("field"),
                    error.get("message", ""),
                    error.get("row")
                ))
        except Exception as e:
            logger.warning(f"Error saving validation errors (table may not exist yet): {str(e)}")
            # Don't fail the whole transaction if errors table doesn't exist
    
    async def get_file_metadata(self, file_id: int) -> Optional[FileUpload]:
        """Get file metadata by ID."""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, filename, s3_key, s3_bucket, uploaded_by, uploaded_at, row_count, has_errors, error_count
                FROM file_uploads
                WHERE id = ?
            """, (file_id,))
            
            row = cursor.fetchone()
            if row:
                return FileUpload(
                    id=row[0],
                    filename=row[1],
                    s3_key=row[2],
                    s3_bucket=row[3],
                    uploaded_by=row[4],
                    uploaded_at=row[5],
                    row_count=row[6]
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting file metadata: {str(e)}")
            raise Exception(f"Failed to get file metadata: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

