"""History controller."""

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime
from app.interfaces.schemas.history_schema import HistoryResponse, EventResponse
from app.application.use_cases.history_use_cases import HistoryUseCases


class HistoryController:
    """
    Controlador para operaciones de historial de eventos.
    
    ¿Qué hace la clase?
    Maneja la lógica de consulta y exportación del historial de eventos,
    incluyendo filtros avanzados y exportación a Excel.
    
    ¿Qué métodos tiene?
    - get_history: Obtiene historial de eventos con filtros y paginación
    - export_history: Exporta historial de eventos a Excel
    """
    
    def __init__(self, history_use_case: HistoryUseCases):
        """
        Inicializa el controlador con el caso de uso de historial.
        
        ¿Qué parámetros recibe y de qué tipo?
        - history_use_case (HistoryUseCases): Instancia del caso de uso de historial
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
        self.history_use_case = history_use_case
    
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
    ) -> HistoryResponse:
        """
        Obtiene historial de eventos con filtros y paginación.
        
        ¿Qué hace la función?
        Consulta el historial de eventos desde la base de datos aplicando
        filtros opcionales y retorna los resultados paginados.
        
        ¿Qué parámetros recibe y de qué tipo?
        - event_type (str | None): Filtro por tipo de evento (DOCUMENT_UPLOAD, AI_PROCESSING, USER_INTERACTION)
        - document_id (int | None): Filtro por ID de documento específico
        - user_id (int | None): Filtro por ID de usuario
        - classification (str | None): Filtro por clasificación de documento (FACTURA, INFORMACIÓN)
        - date_from (datetime | None): Filtro por fecha desde
        - date_to (datetime | None): Filtro por fecha hasta
        - description_search (str | None): Búsqueda en descripción del evento
        - page (int): Número de página (default: 1)
        - page_size (int): Items por página (default: 50, max: 100)
        
        ¿Qué dato regresa y de qué tipo?
        - HistoryResponse: Historial de eventos con información de paginación
        
        Raises:
            HTTPException: Si hay un error al obtener el historial
        """
        try:
            result = await self.history_use_case.get_history(
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
            
            # Convert to response model
            events = [
                EventResponse(
                    id=e["id"],
                    event_type=e["event_type"],
                    description=e["description"],
                    document_id=e.get("document_id"),
                    document_filename=e.get("document_filename"),
                    document_classification=e.get("document_classification"),
                    user_id=e.get("user_id"),
                    created_at=e["created_at"]
                )
                for e in result["events"]
            ]
            
            return HistoryResponse(
                events=events,
                total=result["total"],
                page=result["page"],
                page_size=result["page_size"],
                total_pages=result["total_pages"]
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error getting history: {str(e)}"
            )
    
    async def export_history(
        self,
        event_type: Optional[str] = None,
        document_id: Optional[int] = None,
        user_id: Optional[int] = None,
        classification: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        description_search: Optional[str] = None,
        include_document_details: bool = True
    ) -> StreamingResponse:
        """
        Exporta historial de eventos a archivo Excel.
        
        ¿Qué hace la función?
        Genera un archivo Excel (.xlsx) con el historial de eventos aplicando
        los mismos filtros que el endpoint de consulta.
        
        ¿Qué parámetros recibe y de qué tipo?
        - event_type (str | None): Filtro por tipo de evento
        - document_id (int | None): Filtro por ID de documento
        - user_id (int | None): Filtro por ID de usuario
        - classification (str | None): Filtro por clasificación
        - date_from (datetime | None): Filtro por fecha desde
        - date_to (datetime | None): Filtro por fecha hasta
        - description_search (str | None): Búsqueda en descripción
        - include_document_details (bool): Incluir detalles del documento en exportación (default: True)
        
        ¿Qué dato regresa y de qué tipo?
        - StreamingResponse: Archivo Excel descargable (.xlsx)
        
        Raises:
            HTTPException: Si hay un error al exportar el historial
        """
        try:
            excel_buffer = await self.history_use_case.export_to_excel(
                event_type=event_type,
                document_id=document_id,
                user_id=user_id,
                classification=classification,
                date_from=date_from,
                date_to=date_to,
                description_search=description_search,
                include_document_details=include_document_details
            )
            
            filename = f"historial_eventos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            return StreamingResponse(
                excel_buffer,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error exporting history: {str(e)}"
            )

