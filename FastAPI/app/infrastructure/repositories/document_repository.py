"""
Document repository implementation using SQLAlchemy.

Refactorización con Auto (Claude/ChatGPT) - Migración a SQLAlchemy ORM

¿Qué hace este módulo?
Implementa el repositorio de documentos usando SQLAlchemy ORM en lugar de queries SQL directas.
Mantiene la misma interfaz que la implementación anterior para compatibilidad.

¿Qué clases contiene?
- DocumentRepositoryImpl: Implementación del repositorio usando SQLAlchemy
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.domain.entities.document import Document, Event
from app.domain.repositories.document_repository import DocumentRepository
from app.infrastructure.database.database import get_session
from app.infrastructure.database.models import (
    Document as DocumentModel,
    DocumentExtractedData as DocumentExtractedDataModel,
    LogEvent as LogEventModel
)

logger = logging.getLogger(__name__)


def _document_model_to_entity(model: DocumentModel, extracted_data: Optional[Dict[str, Any]] = None) -> Document:
    """
    Convierte un modelo SQLAlchemy Document a una entidad de dominio Document.
    
    ¿Qué hace la función?
    Transforma un modelo de base de datos (SQLAlchemy) en una entidad de dominio,
    incluyendo los datos extraídos si están disponibles.
    
    ¿Qué parámetros recibe y de qué tipo?
    - model (DocumentModel): Modelo SQLAlchemy de Document
    - extracted_data (Optional[Dict[str, Any]]): Datos extraídos del documento
    
    ¿Qué dato regresa y de qué tipo?
    - Document: Entidad de dominio Document
    """
    return Document(
        id=model.id,
        filename=model.filename,
        original_filename=model.original_filename,
        file_type=model.file_type,
        s3_key=model.s3_key,
        s3_bucket=model.s3_bucket,
        classification=model.classification,
        uploaded_by=model.uploaded_by,
        uploaded_at=model.uploaded_at,
        processed_at=model.processed_at,
        file_size=model.file_size,
        extracted_data=extracted_data
    )


def _event_model_to_dict(model: LogEventModel, document_filename: Optional[str] = None, 
                         document_classification: Optional[str] = None) -> Dict[str, Any]:
    """
    Convierte un modelo SQLAlchemy LogEvent a un diccionario.
    
    ¿Qué hace la función?
    Transforma un modelo de base de datos (SQLAlchemy) en un diccionario
    con la información del evento, incluyendo detalles del documento si están disponibles.
    
    ¿Qué parámetros recibe y de qué tipo?
    - model (LogEventModel): Modelo SQLAlchemy de LogEvent
    - document_filename (Optional[str]): Nombre del archivo del documento relacionado
    - document_classification (Optional[str]): Clasificación del documento relacionado
    
    ¿Qué dato regresa y de qué tipo?
    - Dict[str, Any]: Diccionario con la información del evento
    """
    return {
        "id": model.id,
        "event_type": model.event_type,
        "description": model.description,
        "document_id": model.document_id,
        "document_filename": document_filename,
        "document_classification": document_classification,
        "user_id": model.user_id,
        "created_at": model.created_at
    }


class DocumentRepositoryImpl(DocumentRepository):
    """
    Implementación del repositorio de documentos usando SQLAlchemy.
    
    ¿Qué hace la clase?
    Proporciona métodos para guardar, obtener y listar documentos en la base de datos
    usando SQLAlchemy ORM en lugar de queries SQL directas.
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
    
    async def save_document(self, document: Document) -> Document:
        """
        Guarda un documento en la base de datos.
        
        ¿Qué hace la función?
        Guarda un documento nuevo o actualiza uno existente usando SQLAlchemy ORM.
        Si el documento tiene ID, se actualiza; si no, se inserta como nuevo.
        
        ¿Qué parámetros recibe y de qué tipo?
        - document (Document): Entidad del documento a guardar
        
        ¿Qué dato regresa y de qué tipo?
        - Document: Documento guardado con ID y timestamps actualizados
        """
        try:
            with get_session() as session:
                if document.id:
                    # Actualizar documento existente
                    db_document = session.query(DocumentModel).filter(DocumentModel.id == document.id).first()
                    if not db_document:
                        raise Exception(f"Document with id {document.id} not found")
                    
                    db_document.filename = document.filename
                    db_document.original_filename = document.original_filename
                    db_document.file_type = document.file_type
                    db_document.s3_key = document.s3_key
                    db_document.s3_bucket = document.s3_bucket
                    db_document.classification = document.classification
                    db_document.processed_at = document.processed_at
                    db_document.file_size = document.file_size
                    
                    session.commit()
                    return _document_model_to_entity(db_document, document.extracted_data)
                else:
                    # Insertar nuevo documento
                    db_document = DocumentModel(
                        filename=document.filename,
                        original_filename=document.original_filename,
                        file_type=document.file_type,
                        s3_key=document.s3_key,
                        s3_bucket=document.s3_bucket,
                        classification=document.classification,
                        uploaded_by=document.uploaded_by,
                        uploaded_at=datetime.utcnow() if not document.uploaded_at else document.uploaded_at,
                        processed_at=document.processed_at,
                        file_size=document.file_size
                    )
                    
                    session.add(db_document)
                    session.commit()
                    session.refresh(db_document)
                    
                    document.id = db_document.id
                    document.uploaded_at = db_document.uploaded_at
                    
                    return document
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            raise Exception(f"Failed to save document: {str(e)}")
    
    async def get_document(self, document_id: int) -> Optional[Document]:
        """
        Obtiene un documento por su ID.
        
        ¿Qué hace la función?
        Busca un documento en la base de datos por su ID usando SQLAlchemy ORM
        e incluye los datos extraídos asociados si existen.
        
        ¿Qué parámetros recibe y de qué tipo?
        - document_id (int): ID del documento a buscar
        
        ¿Qué dato regresa y de qué tipo?
        - Optional[Document]: Documento encontrado o None si no existe
        """
        try:
            with get_session() as session:
                db_document = session.query(DocumentModel).filter(DocumentModel.id == document_id).first()
                
                if not db_document:
                    return None
                
                # Obtener datos extraídos si existen
                extracted_data = None
                db_extracted = session.query(DocumentExtractedDataModel).filter(
                    DocumentExtractedDataModel.document_id == document_id
                ).order_by(desc(DocumentExtractedDataModel.created_at)).first()
                
                if db_extracted:
                    try:
                        extracted_data = json.loads(db_extracted.extracted_data)
                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Error parsing extracted_data for document {document_id}: {str(e)}")
                        extracted_data = None
                
                return _document_model_to_entity(db_document, extracted_data)
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            raise Exception(f"Failed to get document: {str(e)}")
    
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
        Lista documentos con filtros y paginación.
        
        ¿Qué hace la función?
        Obtiene una lista paginada de documentos con filtros opcionales usando SQLAlchemy ORM.
        Incluye los datos extraídos de cada documento.
        
        ¿Qué parámetros recibe y de qué tipo?
        - user_id (Optional[int]): Filtrar por ID de usuario
        - classification (Optional[str]): Filtrar por clasificación
        - date_from (Optional[str]): Fecha inicial del rango
        - date_to (Optional[str]): Fecha final del rango
        - page (int): Número de página (default: 1)
        - limit (int): Cantidad de resultados por página (default: 20)
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con total, page, limit, documents
        """
        try:
            with get_session() as session:
                # Construir query base
                query = session.query(DocumentModel)
                
                # Aplicar filtros
                filters = []
                if user_id:
                    filters.append(DocumentModel.uploaded_by == user_id)
                if classification:
                    filters.append(DocumentModel.classification == classification)
                if date_from:
                    filters.append(DocumentModel.uploaded_at >= date_from)
                if date_to:
                    filters.append(DocumentModel.uploaded_at <= date_to)
                
                if filters:
                    query = query.filter(and_(*filters))
                
                # Obtener total
                total = query.count()
                
                # Aplicar paginación y ordenamiento
                offset = (page - 1) * limit
                db_documents = query.order_by(desc(DocumentModel.uploaded_at)).offset(offset).limit(limit).all()
                
                # Convertir a entidades y obtener datos extraídos
                documents = []
                for db_doc in db_documents:
                    # Obtener datos extraídos
                    extracted_data = None
                    db_extracted = session.query(DocumentExtractedDataModel).filter(
                        DocumentExtractedDataModel.document_id == db_doc.id
                    ).order_by(desc(DocumentExtractedDataModel.created_at)).first()
                    
                    if db_extracted:
                        try:
                            extracted_data = json.loads(db_extracted.extracted_data)
                        except (json.JSONDecodeError, TypeError) as e:
                            logger.warning(f"Error parsing extracted_data for document {db_doc.id}: {str(e)}")
                            extracted_data = None
                    
                    documents.append(_document_model_to_entity(db_doc, extracted_data))
                
                return {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "documents": documents
                }
        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            raise Exception(f"Failed to list documents: {str(e)}")
    
    async def save_extracted_data(
        self,
        document_id: int,
        data_type: str,
        extracted_data: Dict[str, Any]
    ) -> bool:
        """
        Guarda datos extraídos para un documento.
        
        ¿Qué hace la función?
        Almacena los datos estructurados extraídos de un documento usando SQLAlchemy ORM.
        
        ¿Qué parámetros recibe y de qué tipo?
        - document_id (int): ID del documento
        - data_type (str): Tipo de datos ("INVOICE" o "INFORMATION")
        - extracted_data (Dict[str, Any]): Datos extraídos estructurados
        
        ¿Qué dato regresa y de qué tipo?
        - bool: True si se guardó exitosamente
        """
        try:
            with get_session() as session:
                db_extracted = DocumentExtractedDataModel(
                    document_id=document_id,
                    data_type=data_type,
                    extracted_data=json.dumps(extracted_data, ensure_ascii=False)
                )
                
                session.add(db_extracted)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving extracted data: {str(e)}")
            raise Exception(f"Failed to save extracted data: {str(e)}")
    
    async def save_event(self, event: Event) -> Event:
        """
        Guarda un evento en la base de datos.
        
        ¿Qué hace la función?
        Registra un evento del sistema usando SQLAlchemy ORM.
        
        ¿Qué parámetros recibe y de qué tipo?
        - event (Event): Entidad del evento a guardar
        
        ¿Qué dato regresa y de qué tipo?
        - Event: Evento guardado con ID y timestamp actualizados
        """
        try:
            with get_session() as session:
                db_event = LogEventModel(
                    event_type=event.event_type,
                    description=event.description,
                    document_id=event.document_id,
                    user_id=event.user_id,
                    created_at=datetime.utcnow() if not event.created_at else event.created_at
                )
                
                session.add(db_event)
                session.commit()
                session.refresh(db_event)
                
                event.id = db_event.id
                event.created_at = db_event.created_at
                
                return event
        except Exception as e:
            logger.error(f"Error saving event: {str(e)}")
            raise Exception(f"Failed to save event: {str(e)}")
    
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
        """
        Lista eventos con filtros y paginación.
        
        ¿Qué hace la función?
        Obtiene una lista paginada de eventos del sistema con múltiples filtros usando SQLAlchemy ORM.
        
        ¿Qué parámetros recibe y de qué tipo?
        - event_type (Optional[str]): Filtrar por tipo de evento
        - document_id (Optional[int]): Filtrar por ID de documento
        - user_id (Optional[int]): Filtrar por ID de usuario
        - classification (Optional[str]): Filtrar por clasificación del documento
        - date_from (Optional[datetime]): Fecha inicial del rango
        - date_to (Optional[datetime]): Fecha final del rango
        - description_search (Optional[str]): Búsqueda de texto en descripción
        - page (int): Número de página (default: 1)
        - page_size (int): Cantidad de resultados por página (default: 50)
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con total, page, page_size, total_pages, events
        """
        try:
            with get_session() as session:
                # Construir query base con JOIN
                from app.infrastructure.database.models import Document as DocumentModel
                query = session.query(
                    LogEventModel,
                    DocumentModel.filename,
                    DocumentModel.classification
                ).outerjoin(DocumentModel, LogEventModel.document_id == DocumentModel.id)
                
                # Aplicar filtros
                filters = []
                if event_type:
                    filters.append(LogEventModel.event_type == event_type)
                if document_id:
                    filters.append(LogEventModel.document_id == document_id)
                if user_id:
                    filters.append(LogEventModel.user_id == user_id)
                if classification:
                    filters.append(DocumentModel.classification == classification)
                if date_from:
                    filters.append(LogEventModel.created_at >= date_from)
                if date_to:
                    filters.append(LogEventModel.created_at <= date_to)
                if description_search:
                    filters.append(LogEventModel.description.like(f"%{description_search}%"))
                
                if filters:
                    query = query.filter(and_(*filters))
                
                # Obtener total
                total = query.count()
                
                # Calcular paginación
                total_pages = (total + page_size - 1) // page_size
                offset = (page - 1) * page_size
                
                # Obtener eventos paginados
                results = query.order_by(desc(LogEventModel.created_at)).offset(offset).limit(page_size).all()
                
                # Convertir a diccionarios
                events = []
                for result in results:
                    db_event, doc_filename, doc_classification = result
                    events.append(_event_model_to_dict(db_event, doc_filename, doc_classification))
                
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

