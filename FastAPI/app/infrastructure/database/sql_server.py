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
            
            # Insert file metadata
            cursor.execute("""
                INSERT INTO file_uploads (filename, s3_key, s3_bucket, uploaded_by, uploaded_at, row_count)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metadata.filename,
                metadata.s3_key,
                metadata.s3_bucket,
                metadata.uploaded_by,
                datetime.utcnow(),
                len(file_data)
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
            
            conn.commit()
            logger.info(f"File data saved to database. File ID: {file_id}, Rows: {len(file_data)}")
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
    
    async def get_file_metadata(self, file_id: int) -> Optional[FileUpload]:
        """Get file metadata by ID."""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, filename, s3_key, s3_bucket, uploaded_by, uploaded_at, row_count
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

