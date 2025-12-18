"""PostgreSQL database service."""

import json
import logging
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from datetime import datetime

from app.core.config import settings
from app.domain.entities.file_upload import FileUpload

logger = logging.getLogger(__name__)


class PostgreSQLService:
    """Service for PostgreSQL operations."""
    
    def __init__(self):
        """Initialize PostgreSQL connection."""
        self.connection_string = settings.postgres_connection_string
        self.pool = None
    
    def get_connection(self):
        """Get database connection."""
        try:
            if self.pool is None:
                # Create connection pool
                self.pool = SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    dsn=self.connection_string
                )
            
            return self.pool.getconn()
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {str(e)}")
            raise Exception(f"Failed to connect to PostgreSQL: {str(e)}")
    
    def return_connection(self, conn):
        """Return connection to pool."""
        if self.pool:
            self.pool.putconn(conn)
    
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
            
            # Ensure tables exist
            self._ensure_tables_exist(cursor)
            conn.commit()
            
            # Insert file metadata
            cursor.execute("""
                INSERT INTO file_uploads (filename, s3_key, s3_bucket, uploaded_by, uploaded_at, row_count)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
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
                # Prepare batch insert
                for row in file_data:
                    row_json = json.dumps(row, ensure_ascii=False)
                    cursor.execute("""
                        INSERT INTO file_data (file_id, row_data)
                        VALUES (%s, %s::jsonb)
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
                self.return_connection(conn)
    
    def _ensure_tables_exist(self, cursor):
        """Ensure tables exist (they should be created by init.sql, but this is a safety check)."""
        try:
            # Check if file_uploads exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'file_uploads'
                )
            """)
            
            if not cursor.fetchone()[0]:
                logger.warning("Table file_uploads does not exist. Creating...")
                cursor.execute("""
                    CREATE TABLE file_uploads (
                        id SERIAL PRIMARY KEY,
                        filename VARCHAR(255) NOT NULL,
                        s3_key VARCHAR(500),
                        s3_bucket VARCHAR(255),
                        uploaded_by INTEGER,
                        uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        row_count INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            # Check if file_data exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'file_data'
                )
            """)
            
            if not cursor.fetchone()[0]:
                logger.warning("Table file_data does not exist. Creating...")
                cursor.execute("""
                    CREATE TABLE file_data (
                        id SERIAL PRIMARY KEY,
                        file_id INTEGER NOT NULL,
                        row_data JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT fk_file_data_file_uploads 
                            FOREIGN KEY (file_id) 
                            REFERENCES file_uploads(id) 
                            ON DELETE CASCADE
                    )
                """)
                
        except Exception as e:
            logger.warning(f"Error ensuring tables exist (may already exist): {str(e)}")
    
    async def get_file_metadata(self, file_id: int) -> Optional[FileUpload]:
        """Get file metadata by ID."""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, filename, s3_key, s3_bucket, uploaded_by, uploaded_at, row_count
                FROM file_uploads
                WHERE id = %s
            """, (file_id,))
            
            row = cursor.fetchone()
            if row:
                return FileUpload(
                    id=row['id'],
                    filename=row['filename'],
                    s3_key=row['s3_key'],
                    s3_bucket=row['s3_bucket'],
                    uploaded_by=row['uploaded_by'],
                    uploaded_at=row['uploaded_at'],
                    row_count=row['row_count']
                )
            return None
            
        except Exception as e:
            logger.error(f"Error getting file metadata: {str(e)}")
            raise Exception(f"Failed to get file metadata: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.return_connection(conn)

