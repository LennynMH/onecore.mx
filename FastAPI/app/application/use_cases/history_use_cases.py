"""
History use cases.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.1

¿Qué hace este módulo?
Maneja la lógica de negocio para el módulo histórico, incluyendo obtención
de eventos con filtros y exportación a Excel. Esta refactorización utiliza
ExcelExporter para mejorar la modularidad.

¿Qué clases contiene?
- HistoryUseCases: Casos de uso para el módulo histórico
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from io import BytesIO

from app.domain.repositories.document_repository import DocumentRepository
from app.application.utils import ExcelExporter

logger = logging.getLogger(__name__)


class HistoryUseCases:
    """History use cases."""
    
    def __init__(self, document_repository: DocumentRepository):
        """Initialize use cases with repository."""
        self.document_repository = document_repository
    
    async def get_history(
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
        Get history with filters and pagination.
        
        Args:
            event_type: Filter by event type
            document_id: Filter by document ID
            user_id: Filter by user ID
            classification: Filter by document classification
            date_from: Filter events from this date
            date_to: Filter events to this date
            description_search: Search in event description
            page: Page number
            page_size: Items per page
            
        Returns:
            Dictionary with events and pagination info
        """
        try:
            result = await self.document_repository.list_events(
                event_type=event_type,
                document_id=document_id,
                user_id=user_id,
                classification=classification,
                date_from=date_from,
                date_to=date_to,
                description_search=description_search,
                page=page,
                page_size=page_size
            )
            
            logger.info(f"History retrieved: {result['total']} total events, page {page}/{result['total_pages']}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting history: {str(e)}")
            raise Exception(f"Failed to get history: {str(e)}")
    
    async def export_to_excel(
        self,
        event_type: Optional[str] = None,
        document_id: Optional[int] = None,
        user_id: Optional[int] = None,
        classification: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        description_search: Optional[str] = None,
        include_document_details: bool = True
    ) -> BytesIO:
        """
        Exporta el historial de eventos a un archivo Excel.
        
        ¿Qué hace la función?
        Obtiene todos los eventos que cumplen los filtros especificados y los
        exporta a un archivo Excel con formato profesional usando ExcelExporter.
        
        ¿Qué parámetros recibe y de qué tipo?
        - event_type (Optional[str]): Filtrar por tipo de evento
        - document_id (Optional[int]): Filtrar por ID de documento
        - user_id (Optional[int]): Filtrar por ID de usuario
        - classification (Optional[str]): Filtrar por clasificación del documento
        - date_from (Optional[datetime]): Filtrar eventos desde esta fecha
        - date_to (Optional[datetime]): Filtrar eventos hasta esta fecha
        - description_search (Optional[str]): Buscar texto en descripción
        - include_document_details (bool): Incluir detalles del documento en exportación (default: True)
        
        ¿Qué dato regresa y de qué tipo?
        - BytesIO: Buffer con el contenido del archivo Excel
        
        Raises:
            Exception: Si ocurre un error durante la exportación
        """
        try:
            # Obtener todos los eventos (sin paginación para exportación)
            result = await self.document_repository.list_events(
                event_type=event_type,
                document_id=document_id,
                user_id=user_id,
                classification=classification,
                date_from=date_from,
                date_to=date_to,
                description_search=description_search,
                page=1,
                page_size=10000  # Límite grande para exportación
            )
            
            events = result.get("events", [])
            
            # Exportar a Excel usando ExcelExporter
            return ExcelExporter.export_events(
                events=events,
                include_document_details=include_document_details,
                sheet_name="Historial de Eventos"
            )
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            raise Exception(f"Failed to export to Excel: {str(e)}")

