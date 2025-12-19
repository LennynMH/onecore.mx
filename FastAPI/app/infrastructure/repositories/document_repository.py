"""
Document repository implementation.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.1

¿Qué hace este módulo?
Implementa el repositorio de documentos usando SQL Server.
Esta refactorización utiliza DatabaseHelper para eliminar código duplicado
de manejo de conexiones y transacciones.

¿Qué clases contiene?
- DocumentRepositoryImpl: Implementación del repositorio de documentos
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.domain.entities.document import Document, Event
from app.domain.repositories.document_repository import DocumentRepository
from app.infrastructure.database.sql_server import SQLServerService
from app.infrastructure.database.db_helper import DatabaseHelper

logger = logging.getLogger(__name__)


class DocumentRepositoryImpl(DocumentRepository):
    """
    Implementación del repositorio de documentos.
    
    ¿Qué hace la clase?
    Proporciona métodos para guardar, obtener y listar documentos en la base de datos,
    así como para guardar datos extraídos y eventos relacionados.
    """
    
    def __init__(self, db_service: SQLServerService):
        """
        Inicializa el repositorio con el servicio de base de datos.
        
        ¿Qué hace la función?
        Configura el repositorio con el servicio de base de datos y crea
        un helper para operaciones comunes.
        
        ¿Qué parámetros recibe y de qué tipo?
        - db_service (SQLServerService): Servicio de base de datos SQL Server
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
        self.db_service = db_service
        self.db_helper = DatabaseHelper(db_service)
    
    async def save_document(self, document: Document) -> Document:
        """
        Guarda un documento en la base de datos.
        
        ¿Qué hace la función?
        Guarda un documento nuevo o actualiza uno existente en la base de datos.
        Si el documento tiene ID, se actualiza; si no, se inserta como nuevo.
        
        ¿Qué parámetros recibe y de qué tipo?
        - document (Document): Entidad del documento a guardar
        
        ¿Qué dato regresa y de qué tipo?
        - Document: Documento guardado con ID y timestamps actualizados
        """
        try:
            with self.db_helper.get_connection() as (conn, cursor):
                if document.id:
                    # Actualizar documento existente
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
                    return document
                else:
                    # Insertar nuevo documento
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
                    
                    return document
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            raise Exception(f"Failed to save document: {str(e)}")
    
    async def get_document(self, document_id: int) -> Optional[Document]:
        """
        Obtiene un documento por su ID.
        
        ¿Qué hace la función?
        Busca un documento en la base de datos por su ID e incluye los datos
        extraídos asociados si existen.
        
        ¿Qué parámetros recibe y de qué tipo?
        - document_id (int): ID del documento a buscar
        
        ¿Qué dato regresa y de qué tipo?
        - Optional[Document]: Documento encontrado o None si no existe
        """
        try:
            with self.db_helper.get_connection() as (conn, cursor):
                cursor.execute("""
                    SELECT id, filename, original_filename, file_type, s3_key, s3_bucket,
                           classification, uploaded_by, uploaded_at, processed_at, file_size
                    FROM documents
                    WHERE id = ?
                """, (document_id,))
                
                row = cursor.fetchone()
                if row:
                    # Obtener datos extraídos si existen
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
        Obtiene una lista paginada de documentos con filtros opcionales por usuario,
        clasificación y rango de fechas. Incluye los datos extraídos de cada documento.
        
        ¿Qué parámetros recibe y de qué tipo?
        - user_id (Optional[int]): Filtrar por ID de usuario
        - classification (Optional[str]): Filtrar por clasificación
        - date_from (Optional[str]): Fecha inicial del rango
        - date_to (Optional[str]): Fecha final del rango
        - page (int): Número de página (default: 1)
        - limit (int): Cantidad de resultados por página (default: 20)
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con:
          - total: Total de documentos que cumplen los filtros
          - page: Página actual
          - limit: Límite por página
          - documents: Lista de documentos
        """
        try:
            with self.db_helper.get_connection() as (conn, cursor):
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
                    document_id = row[0]
                    
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
                        try:
                            extracted_data = json.loads(extracted_row[1])
                        except (json.JSONDecodeError, TypeError) as e:
                            logger.warning(f"Error parsing extracted_data for document {document_id}: {str(e)}")
                            extracted_data = None
                    
                    documents.append(Document(
                        id=document_id,
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
    
    async def save_extracted_data(
        self,
        document_id: int,
        data_type: str,
        extracted_data: Dict[str, Any]
    ) -> bool:
        """
        Guarda datos extraídos para un documento.
        
        ¿Qué hace la función?
        Almacena los datos estructurados extraídos de un documento (factura o información)
        en la base de datos en formato JSON.
        
        ¿Qué parámetros recibe y de qué tipo?
        - document_id (int): ID del documento
        - data_type (str): Tipo de datos ("INVOICE" o "INFORMATION")
        - extracted_data (Dict[str, Any]): Datos extraídos estructurados
        
        ¿Qué dato regresa y de qué tipo?
        - bool: True si se guardó exitosamente
        """
        try:
            with self.db_helper.get_connection() as (conn, cursor):
                cursor.execute("""
                    INSERT INTO document_extracted_data (document_id, data_type, extracted_data)
                    VALUES (?, ?, ?)
                """, (
                    document_id,
                    data_type,
                    json.dumps(extracted_data, ensure_ascii=False)
                ))
                return True
        except Exception as e:
            logger.error(f"Error saving extracted data: {str(e)}")
            raise Exception(f"Failed to save extracted data: {str(e)}")
    
    async def save_event(self, event: Event) -> Event:
        """
        Guarda un evento en la base de datos.
        
        ¿Qué hace la función?
        Registra un evento del sistema (DOCUMENT_UPLOAD, AI_PROCESSING, etc.)
        en la tabla de eventos con timestamps automáticos.
        
        ¿Qué parámetros recibe y de qué tipo?
        - event (Event): Entidad del evento a guardar
        
        ¿Qué dato regresa y de qué tipo?
        - Event: Evento guardado con ID y timestamp actualizados
        """
        try:
            with self.db_helper.get_connection() as (conn, cursor):
                cursor.execute("""
                    INSERT INTO log_events (event_type, description, document_id, user_id, created_at)
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
        Obtiene una lista paginada de eventos del sistema con múltiples filtros opcionales
        (tipo, documento, usuario, clasificación, fechas, búsqueda en descripción).
        
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
        - Dict[str, Any]: Diccionario con:
          - total: Total de eventos que cumplen los filtros
          - page: Página actual
          - page_size: Tamaño de página
          - total_pages: Total de páginas
          - events: Lista de eventos
        """
        try:
            with self.db_helper.get_connection() as (conn, cursor):
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
                    FROM log_events e
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
                    FROM log_events e
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

