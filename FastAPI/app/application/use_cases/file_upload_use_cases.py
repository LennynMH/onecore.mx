"""
File upload use cases.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.1

¿Qué hace este módulo?
Maneja la lógica de negocio para la carga y validación de archivos CSV,
incluyendo subida a S3, validación de datos, y almacenamiento en base de datos.
Esta refactorización utiliza CSVRowValidator para mejorar la modularidad.

¿Qué clases contiene?
- FileUploadUseCases: Casos de uso para carga de archivos CSV
"""

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
from app.application.validators import CSVRowValidator

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
        Sube un archivo CSV, lo valida y lo guarda en S3 y base de datos.
        
        ¿Qué hace la función?
        Procesa un archivo CSV completo: lee el contenido, valida cada fila usando CSVRowValidator
        (valores vacíos, tipos de datos, duplicados), genera un nombre único con timestamp,
        intenta subirlo a S3 (opcional), y guarda los datos validados en la base de datos.
        Retorna un diccionario con el resultado de la operación y todos los errores encontrados.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file (UploadFile): Archivo CSV a subir (FastAPI UploadFile)
        - param1 (str): Primer parámetro adicional a agregar a cada fila
        - param2 (str): Segundo parámetro adicional a agregar a cada fila
        - user_id (int): ID del usuario que está subiendo el archivo
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con:
          - success (bool): True si la operación fue exitosa
          - message (str): Mensaje descriptivo del resultado
          - filename (str): Nombre único del archivo con timestamp
          - original_filename (str): Nombre original del archivo
          - s3_key (str | None): Clave S3 si se subió exitosamente
          - s3_bucket (str | None): Bucket S3 si se subió exitosamente
          - rows_processed (int): Número de filas procesadas exitosamente
          - validation_errors (List[Dict]): Lista de errores de validación encontrados
          - param1 (str): Primer parámetro adicional
          - param2 (str): Segundo parámetro adicional
        
        Raises:
            Exception: Si ocurre un error durante el procesamiento del archivo
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
                
                # Validate row using CSVRowValidator
                row_errors = CSVRowValidator.validate_row(row_data, row_number)
                
                # Check for duplicates using CSVRowValidator
                duplicate_errors = CSVRowValidator.check_duplicates(row_data, row_number, seen_rows)
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

