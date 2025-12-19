"""
Document Processor - Procesador de documentos con clasificación y extracción de datos.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.1

¿Qué hace este módulo?
Proporciona una clase dedicada para procesar documentos completos, incluyendo
clasificación con Textract, extracción de datos estructurados, y registro de eventos.
Esta refactorización extrae la lógica compleja de DocumentUploadUseCases.

¿Qué clases contiene?
- DocumentProcessor: Clase principal para procesamiento completo de documentos
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import UploadFile

from app.domain.entities.document import Document, Event
from app.domain.repositories.document_repository import DocumentRepository
from app.infrastructure.ai.textract_service import TextractService
from app.infrastructure.ai.openai_service import OpenAIService
from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Procesador de documentos con clasificación y extracción de datos.
    
    ¿Qué hace la clase?
    Maneja el flujo completo de procesamiento de documentos: clasificación con Textract,
    extracción de datos estructurados (facturas o información), integración con OpenAI
    para análisis de sentimiento, y registro de eventos en el sistema.
    
    ¿Qué métodos tiene?
    - classify_document: Clasifica documento usando Textract
    - extract_data: Extrae datos estructurados según clasificación
    - register_events: Registra eventos en el sistema
    """
    
    def __init__(
        self,
        textract_service: TextractService,
        document_repository: DocumentRepository,
        openai_service: Optional[OpenAIService] = None
    ):
        """
        Inicializa el procesador de documentos.
        
        ¿Qué hace la función?
        Configura el procesador con los servicios necesarios para clasificación
        y extracción de datos.
        
        ¿Qué parámetros recibe y de qué tipo?
        - textract_service (TextractService): Servicio para análisis con Textract
        - document_repository (DocumentRepository): Repositorio para guardar datos
        - openai_service (Optional[OpenAIService]): Servicio OpenAI para análisis de sentimiento
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
        self.textract_service = textract_service
        self.document_repository = document_repository
        self.openai_service = openai_service
    
    async def classify_document(
        self,
        file: UploadFile,
        s3_key: Optional[str] = None,
        s3_bucket: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clasifica un documento usando AWS Textract.
        
        ¿Qué hace la función?
        Analiza el documento con Textract para determinar si es una FACTURA o
        documento de INFORMACIÓN, retornando el resultado del análisis completo.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file (UploadFile): Archivo del documento a clasificar
        - s3_key (Optional[str]): Clave S3 si el archivo está en S3
        - s3_bucket (Optional[str]): Nombre del bucket S3
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con resultado del análisis:
          - classification: "FACTURA" o "INFORMACIÓN"
          - processing_time_ms: Tiempo de procesamiento en milisegundos
          - confidence: Nivel de confianza (0-100)
          - raw_text: Texto extraído del documento
          - error: Mensaje de error si ocurrió alguno
        """
        classification = None
        processing_time_ms = None
        analysis_result = None
        
        try:
            if settings.aws_textract_enabled:
                logger.info("Starting document classification with AWS Textract...")
                analysis_result = await self.textract_service.analyze_document(
                    file=file,
                    s3_key=s3_key,
                    s3_bucket=s3_bucket
                )
                classification = analysis_result.get("classification", "INFORMACIÓN")
                processing_time_ms = analysis_result.get("processing_time_ms", 0)
                
                if analysis_result.get("error"):
                    logger.warning(f"Textract analysis completed with errors: {analysis_result.get('error')}")
                else:
                    logger.info(f"Document classified as: {classification} (confidence: {analysis_result.get('confidence', 0):.2f}%)")
            else:
                logger.info("AWS Textract is disabled. Skipping classification.")
        except Exception as e:
            logger.warning(f"Error during document classification: {str(e)}. Continuing with upload.")
            classification = "INFORMACIÓN"  # Clasificación por defecto
        
        return {
            "classification": classification,
            "processing_time_ms": processing_time_ms,
            "analysis_result": analysis_result
        }
    
    async def extract_data(
        self,
        file: UploadFile,
        classification: str,
        document_id: int,
        analysis_result: Optional[Dict[str, Any]] = None,
        s3_key: Optional[str] = None,
        s3_bucket: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extrae datos estructurados del documento según su clasificación.
        
        ¿Qué hace la función?
        Procesa el documento según su tipo (FACTURA o INFORMACIÓN) para extraer
        datos estructurados. Para facturas extrae cliente, proveedor, productos, etc.
        Para información extrae descripción, resumen y análisis de sentimiento.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file (UploadFile): Archivo del documento
        - classification (str): Clasificación del documento ("FACTURA" o "INFORMACIÓN")
        - document_id (int): ID del documento en la base de datos
        - analysis_result (Optional[Dict[str, Any]]): Resultado del análisis de Textract
        - s3_key (Optional[str]): Clave S3 si el archivo está en S3
        - s3_bucket (Optional[str]): Nombre del bucket S3
        
        ¿Qué dato regresa y de qué tipo?
        - Optional[Dict[str, Any]]: Datos extraídos estructurados, o None si falla
        """
        extracted_data = None
        
        try:
            raw_text = analysis_result.get("raw_text") if analysis_result else None
            
            if classification == "FACTURA":
                logger.info("Extracting invoice data...")
                # Resetear puntero del archivo para extracción
                await file.seek(0)
                invoice_data = await self.textract_service.extract_invoice_data(
                    file=file,
                    s3_key=s3_key,
                    s3_bucket=s3_bucket,
                    raw_text=raw_text
                )
                
                if invoice_data:
                    # Guardar datos extraídos en base de datos
                    await self.document_repository.save_extracted_data(
                        document_id=document_id,
                        data_type="INVOICE",
                        extracted_data=invoice_data
                    )
                    extracted_data = invoice_data
                    logger.info(f"Invoice data extracted and saved: {len(invoice_data)} fields")
            
            elif classification == "INFORMACIÓN":
                logger.info("Extracting information data...")
                # Resetear puntero del archivo para extracción
                await file.seek(0)
                information_data = await self.textract_service.extract_information_data(
                    file=file,
                    s3_key=s3_key,
                    s3_bucket=s3_bucket,
                    raw_text=raw_text
                )
                
                # Usar OpenAI para análisis de sentimiento si está disponible
                if self.openai_service and information_data.get("resumen"):
                    try:
                        if settings.openai_enabled:
                            logger.info("Analyzing sentiment with OpenAI...")
                            sentiment = await self.openai_service.analyze_sentiment(
                                information_data.get("resumen", "")
                            )
                            information_data["sentimiento"] = sentiment
                            
                            # Generar mejor resumen si OpenAI está disponible
                            if raw_text:
                                summary = await self.openai_service.generate_summary(raw_text)
                                if summary:
                                    information_data["resumen"] = summary
                    except Exception as e:
                        logger.warning(f"Error using OpenAI for sentiment analysis: {str(e)}")
                
                if information_data:
                    # Guardar datos extraídos en base de datos
                    await self.document_repository.save_extracted_data(
                        document_id=document_id,
                        data_type="INFORMATION",
                        extracted_data=information_data
                    )
                    extracted_data = information_data
                    logger.info(f"Information data extracted and saved: {len(information_data)} fields")
            
        except Exception as e:
            logger.warning(f"Error during data extraction: {str(e)}. Continuing without extracted data.")
            # No fallar la subida si la extracción falla
        
        return extracted_data
    
    async def register_events(
        self,
        document: Document,
        user_id: int,
        analysis_result: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra eventos relacionados con el procesamiento del documento.
        
        ¿Qué hace la función?
        Crea y guarda eventos en el sistema para tracking: DOCUMENT_UPLOAD
        cuando se sube el documento, y AI_PROCESSING cuando se clasifica con IA.
        
        ¿Qué parámetros recibe y de qué tipo?
        - document (Document): Entidad del documento procesado
        - user_id (int): ID del usuario que subió el documento
        - analysis_result (Optional[Dict[str, Any]]): Resultado del análisis de Textract
        
        ¿Qué dato regresa y de qué tipo?
        - None: La función no retorna valor, solo registra eventos
        """
        # Registrar evento DOCUMENT_UPLOAD
        try:
            event = Event(
                event_type="DOCUMENT_UPLOAD",
                description=f"Document uploaded: {document.original_filename}",
                document_id=document.id,
                user_id=user_id
            )
            await self.document_repository.save_event(event)
        except Exception as e:
            logger.warning(f"Failed to register DOCUMENT_UPLOAD event: {str(e)}")
        
        # Registrar evento AI_PROCESSING si se realizó clasificación
        if document.classification and analysis_result and not analysis_result.get("error"):
            try:
                ai_event = Event(
                    event_type="AI_PROCESSING",
                    description=f"Document classified as {document.classification} using AWS Textract (confidence: {analysis_result.get('confidence', 0):.2f}%)",
                    document_id=document.id,
                    user_id=user_id
                )
                await self.document_repository.save_event(ai_event)
            except Exception as e:
                logger.warning(f"Failed to register AI_PROCESSING event: {str(e)}")

