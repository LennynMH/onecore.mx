"""File upload use cases."""

import csv
import io
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import UploadFile

from app.domain.entities.file_upload import FileUpload
from app.infrastructure.s3.s3_service import S3Service
from app.domain.repositories.file_repository import FileRepository
from app.core.config import settings

logger = logging.getLogger(__name__)


class FileUploadUseCases:
    """File upload use cases."""
    
    def __init__(
        self,
        s3_service: S3Service,
        file_repository: FileRepository
    ):
        """Initialize use case with services."""
        self.s3_service = s3_service
        self.file_repository = file_repository
    
    @staticmethod
    def _generate_unique_filename(original_filename: str) -> str:
        """
        Generate unique filename with timestamp to avoid duplicates.
        
        Format: nombre_archivo_ddmmyyyyhhmmss.extension
        Example: test.csv -> test_18122025201153.csv
        
        Args:
            original_filename: Original filename from upload
            
        Returns:
            Filename with timestamp suffix
        """
        # Get file name and extension
        name, ext = os.path.splitext(original_filename)
        
        # Generate timestamp: ddmmyyyyhhmmss
        timestamp = datetime.utcnow().strftime('%d%m%Y%H%M%S')
        
        # Combine: nombre_timestamp.extension
        unique_filename = f"{name}_{timestamp}{ext}"
        
        return unique_filename
    
    async def upload_and_validate_file(
        self,
        file: UploadFile,
        param1: str,
        param2: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Upload CSV file, validate it, and save to S3 and database.
        
        Args:
            file: CSV file to upload
            param1: First additional parameter
            param2: Second additional parameter
            user_id: ID of user uploading the file
            
        Returns:
            Dictionary with upload result and validation errors
        """
        validation_errors = []
        
        try:
            # Read and parse CSV file
            # Note: We read the file once here for processing
            # If S3 upload is needed, S3Service will need to read it again
            # So we need to reset the file pointer after reading
            content = await file.read()
            file_content = content.decode('utf-8')
            
            # Reset file pointer for potential S3 upload
            await file.seek(0)
            
            csv_reader = csv.DictReader(io.StringIO(file_content))
            
            # Convert to list of dictionaries
            file_data = []
            row_number = 0  # Empezar en 0, luego incrementar antes de procesar cada fila
            seen_rows = []  # Para detectar duplicados
            
            for row in csv_reader:
                row_number += 1  # Incrementar antes de procesar (primera fila de datos = 1)
                # row_number ahora representa el número de fila de datos (1, 2, 3, ...)
                # No incluye el header en la numeración
                row_data = dict(row)
                
                # Add additional parameters to each row
                row_data['param1'] = param1
                row_data['param2'] = param2
                
                # Validate row
                row_errors = self._validate_row(row_data, row_number)
                
                # Check for duplicates
                duplicate_errors = self._check_duplicates(row_data, row_number, seen_rows)
                if duplicate_errors:
                    validation_errors.extend(duplicate_errors)
                
                if row_errors:
                    validation_errors.extend(row_errors)
                else:
                    # Solo agregar a file_data si no tiene errores
                    # Agregar a seen_rows para detección de duplicados
                    seen_rows.append(row_data)
                    file_data.append(row_data)
            
            # Validate file structure
            if row_number == 0:
                validation_errors.append({
                    "type": "file_structure",
                    "message": "File is empty or has no data rows",
                    "row": None
                })
            
            # Generate unique filename with timestamp to avoid duplicates
            unique_filename = self._generate_unique_filename(file.filename)
            
            # Try to upload to S3 (optional - will continue even if it fails)
            s3_key = None
            s3_bucket = None
            try:
                # Use unique filename in S3 path
                s3_key_path = f"uploads/{datetime.utcnow().strftime('%Y/%m/%d')}/{unique_filename}"
                s3_key = await self.s3_service.upload_file(file, s3_key_path)
                if s3_key:
                    s3_bucket = settings.aws_s3_bucket_name
                    logger.info(f"File successfully uploaded to S3: {s3_key}")
                else:
                    logger.warning("S3 upload skipped (not configured). File will be saved to database only.")
            except Exception as e:
                logger.warning(f"S3 upload failed: {str(e)}. Continuing with database save only.")
                s3_key = None
                s3_bucket = None
            
            # Create file metadata (use unique_filename instead of original filename)
            metadata = FileUpload(
                filename=unique_filename,  # Use unique filename with timestamp
                s3_key=s3_key,
                s3_bucket=s3_bucket,
                uploaded_by=user_id,
                uploaded_at=datetime.utcnow(),
                validation_errors=validation_errors if validation_errors else None,
                row_count=len(file_data)
            )
            
            # Save to database (always, regardless of S3 status)
            await self.file_repository.save_file_data(file_data, metadata)
            
            # Prepare response message
            if s3_key:
                message = "File uploaded successfully to S3 and database"
            else:
                message = "File saved to database (S3 not configured or unavailable)"
            
            return {
                "success": True,
                "message": message,
                "filename": unique_filename,  # Return unique filename with timestamp
                "original_filename": file.filename,  # Keep original for reference
                "s3_key": s3_key,
                "s3_bucket": s3_bucket,
                "rows_processed": len(file_data),
                "validation_errors": validation_errors,
                "param1": param1,
                "param2": param2
            }
            
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}", exc_info=True)
            validation_errors.append({
                "type": "upload_error",
                "message": f"Failed to upload file: {str(e)}",
                "row": None
            })
            raise
    
    def _validate_row(self, row: Dict[str, Any], row_number: int) -> List[Dict[str, Any]]:
        """
        Validate a CSV row.
        
        Args:
            row: Row data as dictionary
            row_number: Row number for error reporting
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for empty values
        for key, value in row.items():
            # Skip param1 and param2 as they are added by the system
            if key in ['param1', 'param2']:
                continue
                
            if value is None or (isinstance(value, str) and value.strip() == ""):
                errors.append({
                    "type": "empty_value",
                    "field": key,
                    "message": f"Empty value in field '{key}'",
                    "row": row_number
                })
        
        # Check for incorrect types
        type_errors = self._validate_types(row, row_number)
        if type_errors:
            errors.extend(type_errors)
        
        return errors
    
    def _validate_types(self, row: Dict[str, Any], row_number: int) -> List[Dict[str, Any]]:
        """
        Validate data types in a CSV row.
        
        Args:
            row: Row data as dictionary
            row_number: Row number for error reporting
            
        Returns:
            List of validation errors for incorrect types
        """
        errors = []
        
        for key, value in row.items():
            # Skip param1 and param2 as they are added by the system
            if key in ['param1', 'param2']:
                continue
            
            if value is None or (isinstance(value, str) and value.strip() == ""):
                continue  # Empty values are handled by _validate_row
            
            # Validate email format
            if key.lower() in ['email', 'e-mail', 'correo']:
                if not self._is_valid_email(value):
                    errors.append({
                        "type": "incorrect_type",
                        "field": key,
                        "message": f"Invalid email format in field '{key}': '{value}'",
                        "row": row_number
                    })
            
            # Validate numeric fields
            elif key.lower() in ['age', 'edad', 'id', 'number', 'numero', 'count', 'cantidad']:
                if not self._is_valid_number(value):
                    errors.append({
                        "type": "incorrect_type",
                        "field": key,
                        "message": f"Invalid number format in field '{key}': '{value}'",
                        "row": row_number
                    })
            
            # Validate date fields
            elif key.lower() in ['date', 'fecha', 'birthdate', 'fecha_nacimiento', 'created_at', 'updated_at']:
                if not self._is_valid_date(value):
                    errors.append({
                        "type": "incorrect_type",
                        "field": key,
                        "message": f"Invalid date format in field '{key}': '{value}'",
                        "row": row_number
                    })
        
        return errors
    
    def _check_duplicates(self, row: Dict[str, Any], row_number: int, seen_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check for duplicate rows.
        
        Args:
            row: Current row data
            row_number: Current row number
            seen_rows: List of previously seen rows
            
        Returns:
            List of validation errors for duplicates
        """
        errors = []
        
        # Create a copy of row without param1 and param2 for comparison
        row_for_comparison = {k: v for k, v in row.items() if k not in ['param1', 'param2']}
        
        # Check if this row is a duplicate
        for idx, seen_row in enumerate(seen_rows):
            seen_row_for_comparison = {k: v for k, v in seen_row.items() if k not in ['param1', 'param2']}
            
            if row_for_comparison == seen_row_for_comparison:
                errors.append({
                    "type": "duplicate",
                    "field": None,
                    "message": f"Duplicate row detected. Row {row_number} is identical to row {idx + 1}",
                    "row": row_number
                })
                break  # Solo reportar el primer duplicado encontrado
        
        return errors
    
    @staticmethod
    def _is_valid_email(value: str) -> bool:
        """Check if value is a valid email format."""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, str(value).strip()))
    
    @staticmethod
    def _is_valid_number(value: Any) -> bool:
        """Check if value is a valid number."""
        try:
            float(str(value).strip())
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def _is_valid_date(value: Any) -> bool:
        """Check if value is a valid date format."""
        from datetime import datetime
        date_formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%m/%d/%Y',
            '%Y-%m-%d %H:%M:%S',
            '%d-%m-%Y',
            '%Y/%m/%d'
        ]
        
        value_str = str(value).strip()
        for fmt in date_formats:
            try:
                datetime.strptime(value_str, fmt)
                return True
            except (ValueError, TypeError):
                continue
        return False

