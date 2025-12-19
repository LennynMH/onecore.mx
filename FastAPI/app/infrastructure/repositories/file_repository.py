"""
File repository implementation using SQLAlchemy.

Refactorización con Auto (Claude/ChatGPT) - Migración a SQLAlchemy ORM

¿Qué hace este módulo?
Implementa el repositorio de archivos usando SQLAlchemy ORM en lugar de queries SQL directas.
Mantiene la misma interfaz que la implementación anterior para compatibilidad.

¿Qué clases contiene?
- FileRepositoryImpl: Implementación del repositorio usando SQLAlchemy
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.domain.entities.file_upload import FileUpload
from app.domain.repositories.file_repository import FileRepository
from app.infrastructure.database.database import get_session
from app.infrastructure.database.models import (
    FileUpload as FileUploadModel,
    FileData as FileDataModel,
    FileValidationError as FileValidationErrorModel
)

logger = logging.getLogger(__name__)


def _file_upload_model_to_entity(model: FileUploadModel, validation_errors: Optional[List[Dict[str, Any]]] = None) -> FileUpload:
    """
    Convierte un modelo SQLAlchemy FileUpload a una entidad de dominio FileUpload.
    
    ¿Qué hace la función?
    Transforma un modelo de base de datos (SQLAlchemy) en una entidad de dominio,
    incluyendo los errores de validación si están disponibles.
    
    ¿Qué parámetros recibe y de qué tipo?
    - model (FileUploadModel): Modelo SQLAlchemy de FileUpload
    - validation_errors (Optional[List[Dict[str, Any]]]): Lista de errores de validación
    
    ¿Qué dato regresa y de qué tipo?
    - FileUpload: Entidad de dominio FileUpload
    """
    return FileUpload(
        id=model.id,
        filename=model.filename,
        s3_key=model.s3_key,
        s3_bucket=model.s3_bucket,
        uploaded_by=model.uploaded_by,
        uploaded_at=model.uploaded_at,
        row_count=model.row_count,
        validation_errors=validation_errors
    )


class FileRepositoryImpl(FileRepository):
    """
    Implementación del repositorio de archivos usando SQLAlchemy.
    
    ¿Qué hace la clase?
    Proporciona métodos para guardar datos de archivos CSV y obtener
    metadatos de archivos desde la base de datos usando SQLAlchemy ORM.
    """
    
    def __init__(self, db_service=None):
        """
        Inicializa el repositorio.
        
        ¿Qué hace la función?
        Inicializa el repositorio. El parámetro db_service se mantiene para compatibilidad
        pero no se usa, ya que SQLAlchemy maneja sus propias conexiones.
        
        ¿Qué parámetros recibe y de qué tipo?
        - db_service: Se mantiene para compatibilidad pero no se usa
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
        # db_service se mantiene para compatibilidad pero no se usa
        pass
    
    async def save_file_data(
        self,
        file_data: List[Dict[str, Any]],
        metadata: FileUpload
    ) -> bool:
        """
        Guarda los datos de un archivo CSV en la base de datos.
        
        ¿Qué hace la función?
        Almacena las filas de datos de un archivo CSV junto con sus metadatos
        (nombre, fecha de carga, errores, etc.) en la base de datos usando SQLAlchemy ORM.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file_data (List[Dict[str, Any]]): Lista de filas de datos del CSV
        - metadata (FileUpload): Metadatos del archivo (nombre, fecha, errores, etc.)
        
        ¿Qué dato regresa y de qué tipo?
        - bool: True si se guardó exitosamente, False en caso contrario
        
        Raises:
            Exception: Si ocurre un error al guardar los datos
        """
        try:
            with get_session() as session:
                # Determinar si el archivo tiene errores
                has_errors = True if metadata.validation_errors and len(metadata.validation_errors) > 0 else False
                error_count = len(metadata.validation_errors) if metadata.validation_errors else 0
                
                # Crear registro de metadatos del archivo
                db_file_upload = FileUploadModel(
                    filename=metadata.filename,
                    s3_key=metadata.s3_key,
                    s3_bucket=metadata.s3_bucket,
                    uploaded_by=metadata.uploaded_by,
                    uploaded_at=metadata.uploaded_at if metadata.uploaded_at else datetime.utcnow(),
                    row_count=len(file_data),
                    has_errors=has_errors,
                    error_count=error_count
                )
                
                session.add(db_file_upload)
                session.flush()  # Para obtener el ID antes del commit
                
                file_id = db_file_upload.id
                
                # Insertar filas de datos
                if file_data:
                    for row in file_data:
                        row_json = json.dumps(row, ensure_ascii=False)
                        db_file_data = FileDataModel(
                            file_id=file_id,
                            row_data=row_json
                        )
                        session.add(db_file_data)
                
                # Insertar errores de validación si existen
                if metadata.validation_errors and len(metadata.validation_errors) > 0:
                    for error in metadata.validation_errors:
                        db_error = FileValidationErrorModel(
                            file_id=file_id,
                            error_type=error.get("type", "unknown"),
                            field_name=error.get("field"),
                            error_message=error.get("message", ""),
                            row_number=error.get("row")
                        )
                        session.add(db_error)
                
                session.commit()
                logger.info(f"File data saved to database. File ID: {file_id}, Rows: {len(file_data)}, Errors: {error_count}")
                return True
        except Exception as e:
            logger.error(f"Error saving file data: {str(e)}")
            raise Exception(f"Failed to save file data: {str(e)}")
    
    async def get_file_metadata(self, file_id: int) -> FileUpload:
        """
        Obtiene los metadatos de un archivo por su ID.
        
        ¿Qué hace la función?
        Busca y retorna los metadatos de un archivo guardado en la base de datos usando SQLAlchemy ORM,
        incluyendo nombre, fecha de carga, estado de errores, etc.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file_id (int): ID del archivo a buscar
        
        ¿Qué dato regresa y de qué tipo?
        - FileUpload: Entidad con los metadatos del archivo
        
        Raises:
            Exception: Si el archivo no existe o hay un error al consultarlo
        """
        try:
            with get_session() as session:
                db_file_upload = session.query(FileUploadModel).filter(
                    FileUploadModel.id == file_id
                ).first()
                
                if not db_file_upload:
                    raise Exception(f"File with id {file_id} not found")
                
                # Obtener errores de validación si existen
                validation_errors = None
                db_errors = session.query(FileValidationErrorModel).filter(
                    FileValidationErrorModel.file_id == file_id
                ).all()
                
                if db_errors:
                    validation_errors = []
                    for db_error in db_errors:
                        validation_errors.append({
                            "type": db_error.error_type,
                            "field": db_error.field_name,
                            "message": db_error.error_message,
                            "row": db_error.row_number
                        })
                
                return _file_upload_model_to_entity(db_file_upload, validation_errors)
        except Exception as e:
            logger.error(f"Error getting file metadata: {str(e)}")
            raise Exception(f"Failed to get file metadata: {str(e)}")
