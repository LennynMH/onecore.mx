"""Document upload controller."""

from fastapi import UploadFile, HTTPException, Query, status
from typing import Optional
from app.interfaces.schemas.document_schema import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentsListResponse
)
from app.application.use_cases.document_upload_use_cases import DocumentUploadUseCases
from app.infrastructure.repositories.document_repository import DocumentRepositoryImpl
from app.infrastructure.database.sql_server import SQLServerService


class DocumentController:
    """
    Controlador para operaciones de documentos.
    
    ¿Qué hace la clase?
    Maneja la lógica de carga, listado y consulta de documentos,
    incluyendo subida a S3, clasificación con IA y extracción de datos.
    
    ¿Qué métodos tiene?
    - upload_document: Sube un documento para análisis
    - list_documents: Lista documentos con filtros y paginación
    - get_document: Obtiene un documento por ID
    """
    
    def __init__(self, document_upload_use_case: DocumentUploadUseCases):
        """
        Inicializa el controlador con el caso de uso de documentos.
        
        ¿Qué parámetros recibe y de qué tipo?
        - document_upload_use_case (DocumentUploadUseCases): Instancia del caso de uso de documentos
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
        self.document_upload_use_case = document_upload_use_case
    
    async def upload_document(
        self,
        file: UploadFile,
        user_id: int
    ) -> DocumentUploadResponse:
        """
        Sube un documento (PDF, JPG, PNG) para análisis.
        
        ¿Qué hace la función?
        Valida el tipo de archivo, lo sube a AWS S3, guarda los metadatos en SQL Server,
        clasifica el documento con AWS Textract y extrae datos estructurados.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file (UploadFile): Archivo de documento a subir (PDF, JPG, PNG)
        - user_id (int): ID del usuario que sube el documento
        
        ¿Qué dato regresa y de qué tipo?
        - DocumentUploadResponse: Resultado de la carga con información del documento
        
        Raises:
            HTTPException: Si el archivo no es válido o hay un error en el proceso
        """
        # Validate file type
        valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        file_extension = None
        if file.filename:
            file_extension = '.' + file.filename.split('.')[-1].lower()
        
        if not file_extension or file_extension not in valid_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a PDF, JPG, or PNG file"
            )
        
        try:
            result = await self.document_upload_use_case.upload_document(
                file=file,
                user_id=user_id
            )
            return DocumentUploadResponse(**result)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading document: {str(e)}"
            )
    
    async def list_documents(
        self,
        user_id: int,
        classification: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> DocumentsListResponse:
        """
        Lista documentos con filtros y paginación.
        
        ¿Qué hace la función?
        Obtiene una lista de documentos del usuario con filtros opcionales
        por clasificación y rango de fechas, con paginación.
        
        ¿Qué parámetros recibe y de qué tipo?
        - user_id (int): ID del usuario autenticado
        - classification (str | None): Filtro por tipo de clasificación (FACTURA, INFORMACIÓN)
        - date_from (str | None): Filtro por fecha desde (YYYY-MM-DD)
        - date_to (str | None): Filtro por fecha hasta (YYYY-MM-DD)
        - page (int): Número de página (default: 1)
        - limit (int): Items por página (default: 20, max: 100)
        
        ¿Qué dato regresa y de qué tipo?
        - DocumentsListResponse: Lista de documentos con información de paginación
        
        Raises:
            HTTPException: Si hay un error al listar documentos
        """
        try:
            db_service = SQLServerService()
            document_repository = DocumentRepositoryImpl(db_service)
            
            result = await document_repository.list_documents(
                user_id=user_id,
                classification=classification,
                date_from=date_from,
                date_to=date_to,
                page=page,
                limit=limit
            )
            
            # Convert Document entities to DocumentResponse
            documents_response = []
            for doc in result["documents"]:
                documents_response.append(DocumentResponse(
                    id=doc.id,
                    filename=doc.filename,
                    original_filename=doc.original_filename,
                    file_type=doc.file_type,
                    classification=doc.classification,
                    uploaded_at=doc.uploaded_at,
                    processed_at=doc.processed_at,
                    extracted_data=doc.extracted_data,
                    s3_key=doc.s3_key,
                    s3_bucket=doc.s3_bucket,
                    file_size=doc.file_size
                ))
            
            return DocumentsListResponse(
                total=result["total"],
                page=result["page"],
                limit=result["limit"],
                documents=documents_response
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error listing documents: {str(e)}"
            )
    
    async def get_document(
        self,
        document_id: int
    ) -> DocumentResponse:
        """
        Obtiene un documento por ID.
        
        ¿Qué hace la función?
        Busca y retorna la información completa de un documento específico,
        incluyendo datos extraídos si están disponibles.
        
        ¿Qué parámetros recibe y de qué tipo?
        - document_id (int): ID del documento a obtener
        
        ¿Qué dato regresa y de qué tipo?
        - DocumentResponse: Información completa del documento
        
        Raises:
            HTTPException: Si el documento no existe o hay un error
        """
        try:
            db_service = SQLServerService()
            document_repository = DocumentRepositoryImpl(db_service)
            
            document = await document_repository.get_document(document_id)
            
            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            
            return DocumentResponse(
                id=document.id,
                filename=document.filename,
                original_filename=document.original_filename,
                file_type=document.file_type,
                classification=document.classification,
                uploaded_at=document.uploaded_at,
                processed_at=document.processed_at,
                extracted_data=document.extracted_data,
                s3_key=document.s3_key,
                s3_bucket=document.s3_bucket,
                file_size=document.file_size
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting document: {str(e)}"
            )

