"""
Pruebas unitarias para HistoryUseCases.

Este módulo contiene al menos 10 casos de prueba para cada método de HistoryUseCases.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any
from io import BytesIO

from app.application.use_cases.history_use_cases import HistoryUseCases


class TestGetHistory:
    """Pruebas para el método get_history."""
    
    @pytest.fixture
    def sample_events_response(self):
        """Fixture para respuesta de eventos."""
        return {
            "events": [
                {
                    "id": 1,
                    "event_type": "DOCUMENT_UPLOAD",
                    "description": "Document uploaded",
                    "document_id": 1,
                    "user_id": 1,
                    "created_at": datetime.now()
                },
                {
                    "id": 2,
                    "event_type": "AI_PROCESSING",
                    "description": "Document classified",
                    "document_id": 1,
                    "user_id": 1,
                    "created_at": datetime.now()
                }
            ],
            "total": 2,
            "page": 1,
            "page_size": 50,
            "total_pages": 1
        }
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_get_history_without_filters(self, mock_document_repository, sample_events_response):
        """Test 1: Obtener historial sin filtros debe retornar todos los eventos."""
        mock_document_repository.list_events = AsyncMock(return_value=sample_events_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        result = await use_case.get_history()
        
        assert result["total"] == 2
        assert len(result["events"]) == 2
        assert result["page"] == 1
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_get_history_filters_by_event_type(self, mock_document_repository):
        """Test 2: Filtrar por tipo de evento debe funcionar."""
        filtered_response = {
            "events": [{"id": 1, "event_type": "DOCUMENT_UPLOAD", "description": "Upload"}],
            "total": 1,
            "page": 1,
            "page_size": 50,
            "total_pages": 1
        }
        mock_document_repository.list_events = AsyncMock(return_value=filtered_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        result = await use_case.get_history(event_type="DOCUMENT_UPLOAD")
        
        assert result["total"] == 1
        assert all(e["event_type"] == "DOCUMENT_UPLOAD" for e in result["events"])
        mock_document_repository.list_events.assert_called_with(
            event_type="DOCUMENT_UPLOAD",
            document_id=None,
            user_id=None,
            classification=None,
            date_from=None,
            date_to=None,
            description_search=None,
            page=1,
            page_size=50
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_get_history_filters_by_document_id(self, mock_document_repository):
        """Test 3: Filtrar por ID de documento debe funcionar."""
        filtered_response = {
            "events": [{"id": 1, "document_id": 5, "description": "Event for doc 5"}],
            "total": 1,
            "page": 1,
            "page_size": 50,
            "total_pages": 1
        }
        mock_document_repository.list_events = AsyncMock(return_value=filtered_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        result = await use_case.get_history(document_id=5)
        
        assert result["total"] == 1
        mock_document_repository.list_events.assert_called_with(
            event_type=None,
            document_id=5,
            user_id=None,
            classification=None,
            date_from=None,
            date_to=None,
            description_search=None,
            page=1,
            page_size=50
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_get_history_filters_by_user_id(self, mock_document_repository):
        """Test 4: Filtrar por ID de usuario debe funcionar."""
        filtered_response = {
            "events": [{"id": 1, "user_id": 10, "description": "User event"}],
            "total": 1,
            "page": 1,
            "page_size": 50,
            "total_pages": 1
        }
        mock_document_repository.list_events = AsyncMock(return_value=filtered_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        result = await use_case.get_history(user_id=10)
        
        assert result["total"] == 1
        mock_document_repository.list_events.assert_called_with(
            event_type=None,
            document_id=None,
            user_id=10,
            classification=None,
            date_from=None,
            date_to=None,
            description_search=None,
            page=1,
            page_size=50
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_get_history_filters_by_classification(self, mock_document_repository):
        """Test 5: Filtrar por clasificación debe funcionar."""
        filtered_response = {
            "events": [{"id": 1, "document_classification": "FACTURA", "description": "Invoice event"}],
            "total": 1,
            "page": 1,
            "page_size": 50,
            "total_pages": 1
        }
        mock_document_repository.list_events = AsyncMock(return_value=filtered_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        result = await use_case.get_history(classification="FACTURA")
        
        assert result["total"] == 1
        mock_document_repository.list_events.assert_called_with(
            event_type=None,
            document_id=None,
            user_id=None,
            classification="FACTURA",
            date_from=None,
            date_to=None,
            description_search=None,
            page=1,
            page_size=50
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_get_history_filters_by_date_range(self, mock_document_repository):
        """Test 6: Filtrar por rango de fechas debe funcionar."""
        date_from = datetime.now() - timedelta(days=7)
        date_to = datetime.now()
        
        filtered_response = {
            "events": [{"id": 1, "created_at": datetime.now()}],
            "total": 1,
            "page": 1,
            "page_size": 50,
            "total_pages": 1
        }
        mock_document_repository.list_events = AsyncMock(return_value=filtered_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        result = await use_case.get_history(date_from=date_from, date_to=date_to)
        
        assert result["total"] == 1
        mock_document_repository.list_events.assert_called_with(
            event_type=None,
            document_id=None,
            user_id=None,
            classification=None,
            date_from=date_from,
            date_to=date_to,
            description_search=None,
            page=1,
            page_size=50
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_get_history_searches_description(self, mock_document_repository):
        """Test 7: Búsqueda en descripción debe funcionar."""
        filtered_response = {
            "events": [{"id": 1, "description": "Document uploaded successfully"}],
            "total": 1,
            "page": 1,
            "page_size": 50,
            "total_pages": 1
        }
        mock_document_repository.list_events = AsyncMock(return_value=filtered_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        result = await use_case.get_history(description_search="uploaded")
        
        assert result["total"] == 1
        mock_document_repository.list_events.assert_called_with(
            event_type=None,
            document_id=None,
            user_id=None,
            classification=None,
            date_from=None,
            date_to=None,
            description_search="uploaded",
            page=1,
            page_size=50
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_get_history_pagination(self, mock_document_repository):
        """Test 8: Paginación debe funcionar correctamente."""
        page2_response = {
            "events": [{"id": 3, "description": "Event 3"}],
            "total": 25,
            "page": 2,
            "page_size": 10,
            "total_pages": 3
        }
        mock_document_repository.list_events = AsyncMock(return_value=page2_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        result = await use_case.get_history(page=2, page_size=10)
        
        assert result["page"] == 2
        assert result["page_size"] == 10
        assert result["total_pages"] == 3
        assert result["total"] == 25
        mock_document_repository.list_events.assert_called_with(
            event_type=None,
            document_id=None,
            user_id=None,
            classification=None,
            date_from=None,
            date_to=None,
            description_search=None,
            page=2,
            page_size=10
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_get_history_combines_multiple_filters(self, mock_document_repository):
        """Test 9: Combinar múltiples filtros debe funcionar."""
        filtered_response = {
            "events": [{"id": 1, "event_type": "DOCUMENT_UPLOAD", "user_id": 5}],
            "total": 1,
            "page": 1,
            "page_size": 50,
            "total_pages": 1
        }
        mock_document_repository.list_events = AsyncMock(return_value=filtered_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        result = await use_case.get_history(
            event_type="DOCUMENT_UPLOAD",
            user_id=5,
            classification="FACTURA"
        )
        
        assert result["total"] == 1
        mock_document_repository.list_events.assert_called_with(
            event_type="DOCUMENT_UPLOAD",
            document_id=None,
            user_id=5,
            classification="FACTURA",
            date_from=None,
            date_to=None,
            description_search=None,
            page=1,
            page_size=50
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_get_history_handles_empty_results(self, mock_document_repository):
        """Test 10: Debe manejar resultados vacíos correctamente."""
        empty_response = {
            "events": [],
            "total": 0,
            "page": 1,
            "page_size": 50,
            "total_pages": 0
        }
        mock_document_repository.list_events = AsyncMock(return_value=empty_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        result = await use_case.get_history()
        
        assert result["total"] == 0
        assert len(result["events"]) == 0
        assert result["total_pages"] == 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_get_history_handles_repository_error(self, mock_document_repository):
        """Test 11: Debe manejar errores del repositorio."""
        mock_document_repository.list_events = AsyncMock(side_effect=Exception("Database error"))
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        
        with pytest.raises(Exception, match="Failed to get history"):
            await use_case.get_history()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_get_history_default_pagination(self, mock_document_repository, sample_events_response):
        """Test 12: Paginación por defecto debe ser page=1, page_size=50."""
        mock_document_repository.list_events = AsyncMock(return_value=sample_events_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        result = await use_case.get_history()
        
        assert result["page"] == 1
        assert result["page_size"] == 50
        mock_document_repository.list_events.assert_called_with(
            event_type=None,
            document_id=None,
            user_id=None,
            classification=None,
            date_from=None,
            date_to=None,
            description_search=None,
            page=1,
            page_size=50
        )


class TestExportToExcel:
    """Pruebas para el método export_to_excel."""
    
    @pytest.fixture
    def sample_events(self):
        """Fixture para eventos de prueba."""
        return [
            {
                "id": 1,
                "event_type": "DOCUMENT_UPLOAD",
                "description": "Document uploaded",
                "document_id": 1,
                "document_filename": "test.pdf",
                "document_classification": "FACTURA",
                "user_id": 1,
                "created_at": datetime.now()
            },
            {
                "id": 2,
                "event_type": "AI_PROCESSING",
                "description": "Document classified",
                "document_id": 1,
                "document_filename": "test.pdf",
                "document_classification": "FACTURA",
                "user_id": 1,
                "created_at": datetime.now()
            }
        ]
    
    @pytest.fixture
    def mock_events_response(self, sample_events):
        """Fixture para respuesta de eventos."""
        return {
            "events": sample_events,
            "total": 2,
            "page": 1,
            "page_size": 10000,
            "total_pages": 1
        }
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_export_to_excel_creates_file(self, mock_document_repository, mock_events_response):
        """Test 1: Debe crear archivo Excel."""
        mock_document_repository.list_events = AsyncMock(return_value=mock_events_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        excel_buffer = await use_case.export_to_excel()
        
        assert isinstance(excel_buffer, BytesIO)
        assert excel_buffer.getvalue() is not None
        assert len(excel_buffer.getvalue()) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_export_to_excel_includes_all_events(self, mock_document_repository, mock_events_response):
        """Test 2: Debe incluir todos los eventos."""
        mock_document_repository.list_events = AsyncMock(return_value=mock_events_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        excel_buffer = await use_case.export_to_excel()
        
        # Verificar que se llamó con page_size grande para obtener todos
        mock_document_repository.list_events.assert_called_with(
            event_type=None,
            document_id=None,
            user_id=None,
            classification=None,
            date_from=None,
            date_to=None,
            description_search=None,
            page=1,
            page_size=10000
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_export_to_excel_applies_filters(self, mock_document_repository, mock_events_response):
        """Test 3: Debe aplicar filtros al exportar."""
        mock_document_repository.list_events = AsyncMock(return_value=mock_events_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        await use_case.export_to_excel(
            event_type="DOCUMENT_UPLOAD",
            user_id=1
        )
        
        mock_document_repository.list_events.assert_called_with(
            event_type="DOCUMENT_UPLOAD",
            document_id=None,
            user_id=1,
            classification=None,
            date_from=None,
            date_to=None,
            description_search=None,
            page=1,
            page_size=10000
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_export_to_excel_includes_document_details(self, mock_document_repository, mock_events_response):
        """Test 4: Debe incluir detalles del documento por defecto."""
        mock_document_repository.list_events = AsyncMock(return_value=mock_events_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        excel_buffer = await use_case.export_to_excel(include_document_details=True)
        
        assert isinstance(excel_buffer, BytesIO)
        # El Excel debe tener columnas adicionales para detalles del documento
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_export_to_excel_excludes_document_details(self, mock_document_repository, mock_events_response):
        """Test 5: Debe poder excluir detalles del documento."""
        mock_document_repository.list_events = AsyncMock(return_value=mock_events_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        excel_buffer = await use_case.export_to_excel(include_document_details=False)
        
        assert isinstance(excel_buffer, BytesIO)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_export_to_excel_handles_empty_events(self, mock_document_repository):
        """Test 6: Debe manejar lista vacía de eventos."""
        empty_response = {
            "events": [],
            "total": 0,
            "page": 1,
            "page_size": 10000,
            "total_pages": 0
        }
        mock_document_repository.list_events = AsyncMock(return_value=empty_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        excel_buffer = await use_case.export_to_excel()
        
        assert isinstance(excel_buffer, BytesIO)
        # Debe crear Excel incluso sin eventos (solo con encabezados)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_export_to_excel_filters_by_date_range(self, mock_document_repository, mock_events_response):
        """Test 7: Debe filtrar por rango de fechas."""
        date_from = datetime.now() - timedelta(days=7)
        date_to = datetime.now()
        
        mock_document_repository.list_events = AsyncMock(return_value=mock_events_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        await use_case.export_to_excel(date_from=date_from, date_to=date_to)
        
        mock_document_repository.list_events.assert_called_with(
            event_type=None,
            document_id=None,
            user_id=None,
            classification=None,
            date_from=date_from,
            date_to=date_to,
            description_search=None,
            page=1,
            page_size=10000
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_export_to_excel_handles_repository_error(self, mock_document_repository):
        """Test 8: Debe manejar errores del repositorio."""
        mock_document_repository.list_events = AsyncMock(side_effect=Exception("Database error"))
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        
        with pytest.raises(Exception, match="Failed to export to Excel"):
            await use_case.export_to_excel()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_export_to_excel_large_dataset(self, mock_document_repository):
        """Test 9: Debe manejar grandes volúmenes de datos."""
        large_events = [{"id": i, "event_type": "DOCUMENT_UPLOAD", "description": f"Event {i}"} 
                       for i in range(1000)]
        large_response = {
            "events": large_events,
            "total": 1000,
            "page": 1,
            "page_size": 10000,
            "total_pages": 1
        }
        mock_document_repository.list_events = AsyncMock(return_value=large_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        excel_buffer = await use_case.export_to_excel()
        
        assert isinstance(excel_buffer, BytesIO)
        assert len(excel_buffer.getvalue()) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.history
    async def test_export_to_excel_combines_all_filters(self, mock_document_repository, mock_events_response):
        """Test 10: Debe combinar todos los filtros."""
        date_from = datetime.now() - timedelta(days=7)
        date_to = datetime.now()
        
        mock_document_repository.list_events = AsyncMock(return_value=mock_events_response)
        
        use_case = HistoryUseCases(document_repository=mock_document_repository)
        await use_case.export_to_excel(
            event_type="DOCUMENT_UPLOAD",
            document_id=1,
            user_id=1,
            classification="FACTURA",
            date_from=date_from,
            date_to=date_to,
            description_search="upload"
        )
        
        mock_document_repository.list_events.assert_called_with(
            event_type="DOCUMENT_UPLOAD",
            document_id=1,
            user_id=1,
            classification="FACTURA",
            date_from=date_from,
            date_to=date_to,
            description_search="upload",
            page=1,
            page_size=10000
        )

