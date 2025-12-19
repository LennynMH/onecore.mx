"""
Document upload use cases.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.1

¿Qué hace este módulo?
Maneja la lógica de negocio para la carga de documentos (PDF, JPG, PNG),
incluyendo subida a S3, clasificación automática, y extracción de datos.
Esta refactorización utiliza FileUtils y DocumentProcessor para mejorar la modularidad.

¿Qué clases contiene?
- DocumentUploadUseCases: Casos de uso para carga de documentos
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import UploadFile

from app.domain.entities.document import Document
from app.domain.repositories.document_repository import DocumentRepository
from app.infrastructure.s3.s3_service import S3Service
from app.infrastructure.ai.textract_service import TextractService
from app.infrastructure.ai.openai_service import OpenAIService
from app.application.utils import FileUtils
from app.application.processors import DocumentProcessor

logger = logging.getLogger(__name__)


class DocumentUploadUseCases:
    """Document upload use cases."""
    
    def __init__(
        self,
        s3_service: S3Service,
        document_repository: DocumentRepository,
        textract_service: Optional[TextractService] = None,
        openai_service: Optional[OpenAIService] = None
    ):
        """
        Inicializa los casos de uso con los servicios necesarios.
        
        ¿Qué hace la función?
        Configura los servicios para subida de documentos, incluyendo S3,
        repositorio de documentos, y servicios de IA (Textract y OpenAI).
        
        ¿Qué parámetros recibe y de qué tipo?
        - s3_service (S3Service): Servicio para subida a S3
        - document_repository (DocumentRepository): Repositorio para guardar documentos
        - textract_service (Optional[TextractService]): Servicio Textract (opcional)
        - openai_service (Optional[OpenAIService]): Servicio OpenAI (opcional)
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
        self.s3_service = s3_service
        self.document_repository = document_repository
        self.textract_service = textract_service or TextractService()
        self.openai_service = openai_service
        
        # Inicializar procesador de documentos
        self.document_processor = DocumentProcessor(
            textract_service=self.textract_service,
            document_repository=self.document_repository,
            openai_service=self.openai_service
        )
    
    async def upload_document(
        self,
        file: UploadFile,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Sube un documento a S3 y base de datos, con clasificación y extracción de datos.
        
        ¿Qué hace la función?
        Procesa un documento completo: valida el tipo, genera nombre único, sube a S3,
        clasifica con Textract, extrae datos estructurados, guarda en BD y registra eventos.
        Usa FileUtils para utilidades de archivos y DocumentProcessor para el flujo de procesamiento.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file (UploadFile): Archivo del documento a subir (PDF, JPG, PNG)
        - user_id (int): ID del usuario que está subiendo el documento
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con resultado de la operación:
          - success (bool): True si la operación fue exitosa
          - message (str): Mensaje descriptivo del resultado
          - document_id (int): ID del documento guardado
          - filename (str): Nombre único del archivo
          - original_filename (str): Nombre original del archivo
          - s3_key (str | None): Clave S3 si se subió exitosamente
          - s3_bucket (str | None): Bucket S3 si se subió exitosamente
          - classification (str | None): Clasificación del documento (FACTURA/INFORMACIÓN)
          - extracted_data (Dict | None): Datos extraídos estructurados
          - processing_time_ms (int | None): Tiempo de procesamiento en milisegundos
        
        Raises:
            ValueError: Si el tipo de archivo no es permitido
            Exception: Si ocurre un error durante el procesamiento
        """
        try:
            # Validar tipo de archivo usando FileUtils
            if not FileUtils.validate_file_type(file.filename, ['PDF', 'JPG', 'PNG']):
                file_type = FileUtils.get_file_type(file.filename)
                raise ValueError(f"Invalid file type: {file_type}. Only PDF, JPG, PNG are allowed.")
            
            file_type = FileUtils.get_file_type(file.filename)
            
            # Generar nombre único usando FileUtils
            unique_filename = FileUtils.generate_unique_filename(file.filename)
            
            # Leer contenido del archivo para obtener tamaño
            file_content = await file.read()
            file_size = len(file_content)
            # Resetear puntero del archivo para subida a S3
            await file.seek(0)
            
            # Intentar subir a S3
            s3_key = None
            s3_bucket = None
            try:
                # Usar FileUtils para generar ruta S3
                s3_key_path = FileUtils.get_s3_path(unique_filename, "documents")
                s3_key = await self.s3_service.upload_file(file, s3_key_path)
                if s3_key:
                    from app.core.config import settings
                    s3_bucket = settings.aws_s3_bucket_name
                    logger.info(f"Document successfully uploaded to S3: {s3_key}")
                else:
                    logger.warning("S3 upload skipped (not configured). Document will be saved to database only.")
            except Exception as e:
                logger.warning(f"S3 upload failed: {str(e)}. Continuing with database save only.")
                s3_key = None
                s3_bucket = None
            
            # Clasificar documento usando DocumentProcessor
            classification_result = await self.document_processor.classify_document(
                file=file,
                s3_key=s3_key,
                s3_bucket=s3_bucket
            )
            classification = classification_result.get("classification")
            processing_time_ms = classification_result.get("processing_time_ms")
            analysis_result = classification_result.get("analysis_result")
            
            # Crear entidad de documento
            processed_at = datetime.utcnow() if classification else None
            document = Document(
                filename=unique_filename,
                original_filename=file.filename,
                file_type=file_type,
                s3_key=s3_key,
                s3_bucket=s3_bucket,
                classification=classification,
                uploaded_by=user_id,
                file_size=file_size,
                processed_at=processed_at
            )
            
            # Guardar documento en base de datos
            document = await self.document_repository.save_document(document)
            
            # Registrar eventos usando DocumentProcessor
            await self.document_processor.register_events(
                document=document,
                user_id=user_id,
                analysis_result=analysis_result
            )
            
            # Extraer datos estructurados usando DocumentProcessor
            extracted_data = await self.document_processor.extract_data(
                file=file,
                classification=classification or "INFORMACIÓN",
                document_id=document.id,
                analysis_result=analysis_result,
                s3_key=s3_key,
                s3_bucket=s3_bucket
            )
            
            return {
                "success": True,
                "message": "Document uploaded successfully to S3 and database",
                "document_id": document.id,
                "filename": document.filename,
                "original_filename": document.original_filename,
                "s3_key": document.s3_key,
                "s3_bucket": document.s3_bucket,
                "classification": document.classification,
                "extracted_data": extracted_data,
                "processing_time_ms": processing_time_ms
            }
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            raise Exception(f"Failed to upload document: {str(e)}")

