"""
Pruebas unitarias para DocumentUploadUseCases.

Este módulo contiene al menos 10 casos de prueba para cada método de DocumentUploadUseCases.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import UploadFile
from io import BytesIO
from typing import Dict, Any

from app.application.use_cases.document_upload_use_cases import DocumentUploadUseCases
from app.domain.entities.document import Document


class TestUploadDocument:
    """Pruebas para el método upload_document."""
    
    @pytest.fixture
    def sample_pdf_file(self):
        """Fixture para archivo PDF."""
        content = b"%PDF-1.4\nTest PDF content"
        return UploadFile(
            filename="test.pdf",
            file=BytesIO(content)
        )
    
    @pytest.fixture
    def sample_jpg_file(self):
        """Fixture para archivo JPG."""
        content = b"\xFF\xD8\xFF\xE0\x00\x10JFIF"  # Header JPG
        return UploadFile(
            filename="test.jpg",
            file=BytesIO(content)
        )
    
    @pytest.fixture
    def sample_png_file(self):
        """Fixture para archivo PNG."""
        content = b"\x89PNG\r\n\x1a\n"  # Header PNG
        return UploadFile(
            filename="test.png",
            file=BytesIO(content)
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.document_upload
    async def test_upload_pdf_success(self, sample_pdf_file, mock_s3_service, mock_document_repository, mock_textract_service):
        """Test 1: Subir PDF válido debe retornar success=True."""
        mock_document_repository.save_document = AsyncMock(return_value=Document(
            id=1,
            filename="test_1234567890.pdf",
            original_filename="test.pdf",
            file_type="PDF",
            classification="FACTURA",
            uploaded_by=1
        ))
        
        use_case = DocumentUploadUseCases(
            s3_service=mock_s3_service,
            document_repository=mock_document_repository,
            textract_service=mock_textract_service
        )
        
        result = await use_case.upload_document(
            file=sample_pdf_file,
            user_id=1
        )
        
        assert result["success"] is True
        assert result["document_id"] == 1
        assert "filename" in result
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.document_upload
    async def test_upload_generates_unique_filename(self, sample_pdf_file, mock_s3_service, mock_document_repository, mock_textract_service):
        """Test 2: Debe generar nombre único con timestamp."""
        mock_document_repository.save_document = AsyncMock(return_value=Document(
            id=1,
            filename="test_1234567890.pdf",
            original_filename="test.pdf",
            file_type="PDF",
            uploaded_by=1
        ))
        
        use_case = DocumentUploadUseCases(
            s3_service=mock_s3_service,
            document_repository=mock_document_repository,
            textract_service=mock_textract_service
        )
        
        result = await use_case.upload_document(
            file=sample_pdf_file,
            user_id=1
        )
        
        assert "_" in result["filename"]
        assert result["filename"].endswith(".pdf")
        assert result["filename"] != "test.pdf"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.document_upload
    async def test_upload_validates_file_type_pdf(self, sample_pdf_file, mock_s3_service, mock_document_repository, mock_textract_service):
        """Test 3: Debe aceptar archivos PDF."""
        mock_document_repository.save_document = AsyncMock(return_value=Document(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_type="PDF",
            uploaded_by=1
        ))
        
        use_case = DocumentUploadUseCases(
            s3_service=mock_s3_service,
            document_repository=mock_document_repository,
            textract_service=mock_textract_service
        )
        
        result = await use_case.upload_document(
            file=sample_pdf_file,
            user_id=1
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.document_upload
    async def test_upload_validates_file_type_jpg(self, sample_jpg_file, mock_s3_service, mock_document_repository, mock_textract_service):
        """Test 4: Debe aceptar archivos JPG."""
        mock_document_repository.save_document = AsyncMock(return_value=Document(
            id=1,
            filename="test.jpg",
            original_filename="test.jpg",
            file_type="JPG",
            uploaded_by=1
        ))
        
        use_case = DocumentUploadUseCases(
            s3_service=mock_s3_service,
            document_repository=mock_document_repository,
            textract_service=mock_textract_service
        )
        
        result = await use_case.upload_document(
            file=sample_jpg_file,
            user_id=1
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.document_upload
    async def test_upload_validates_file_type_png(self, sample_png_file, mock_s3_service, mock_document_repository, mock_textract_service):
        """Test 5: Debe aceptar archivos PNG."""
        mock_document_repository.save_document = AsyncMock(return_value=Document(
            id=1,
            filename="test.png",
            original_filename="test.png",
            file_type="PNG",
            uploaded_by=1
        ))
        
        use_case = DocumentUploadUseCases(
            s3_service=mock_s3_service,
            document_repository=mock_document_repository,
            textract_service=mock_textract_service
        )
        
        result = await use_case.upload_document(
            file=sample_png_file,
            user_id=1
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.document_upload
    async def test_upload_rejects_invalid_file_type(self, mock_s3_service, mock_document_repository, mock_textract_service):
        """Test 6: Debe rechazar tipos de archivo no permitidos."""
        content = b"Invalid file content"
        file = UploadFile(filename="test.txt", file=BytesIO(content))
        
        use_case = DocumentUploadUseCases(
            s3_service=mock_s3_service,
            document_repository=mock_document_repository,
            textract_service=mock_textract_service
        )
        
        with pytest.raises(Exception, match="Invalid file type"):
            await use_case.upload_document(
                file=file,
                user_id=1
            )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.document_upload
    async def test_upload_classifies_document(self, sample_pdf_file, mock_s3_service, mock_document_repository, mock_textract_service):
        """Test 7: Debe clasificar documento con Textract."""
        mock_textract_service.analyze_document = AsyncMock(return_value={
            "classification": "FACTURA",
            "raw_text": "Invoice text",
            "confidence": 95.0,
            "processing_time_ms": 500
        })
        
        mock_document_repository.save_document = AsyncMock(return_value=Document(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_type="PDF",
            classification="FACTURA",
            uploaded_by=1
        ))
        
        use_case = DocumentUploadUseCases(
            s3_service=mock_s3_service,
            document_repository=mock_document_repository,
            textract_service=mock_textract_service
        )
        
        result = await use_case.upload_document(
            file=sample_pdf_file,
            user_id=1
        )
        
        assert result["classification"] == "FACTURA"
        mock_textract_service.analyze_document.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.document_upload
    async def test_upload_extracts_data_for_invoice(self, sample_pdf_file, mock_s3_service, mock_document_repository, mock_textract_service):
        """Test 8: Debe extraer datos para facturas."""
        mock_textract_service.analyze_document = AsyncMock(return_value={
            "classification": "FACTURA",
            "raw_text": "Invoice text",
            "confidence": 95.0,
            "processing_time_ms": 500
        })
        
        mock_textract_service.extract_invoice_data = AsyncMock(return_value={
            "cliente": {"nombre": "Test Client"},
            "proveedor": {"nombre": "Test Provider"},
            "numero_factura": "FAC-001"
        })
        
        mock_document_repository.save_document = AsyncMock(return_value=Document(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_type="PDF",
            classification="FACTURA",
            uploaded_by=1
        ))
        
        use_case = DocumentUploadUseCases(
            s3_service=mock_s3_service,
            document_repository=mock_document_repository,
            textract_service=mock_textract_service
        )
        
        result = await use_case.upload_document(
            file=sample_pdf_file,
            user_id=1
        )
        
        assert result["extracted_data"] is not None
        assert "cliente" in result["extracted_data"]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.document_upload
    async def test_upload_saves_to_s3(self, sample_pdf_file, mock_s3_service, mock_document_repository, mock_textract_service):
        """Test 9: Debe subir a S3 exitosamente."""
        # Configurar S3 para retornar una clave válida
        s3_key_returned = "documents/2025/12/19/test_1234567890.pdf"
        mock_s3_service.upload_file = AsyncMock(return_value=s3_key_returned)
        
        # Configurar mock de Textract para retornar resultado válido sin error
        analysis_result = {
            "classification": "FACTURA",
            "raw_text": "Invoice text",
            "confidence": 95.0,
            "processing_time_ms": 500,
            "error": None
        }
        mock_textract_service.analyze_document = AsyncMock(return_value=analysis_result)
        
        # Configurar extract_data para evitar errores
        mock_textract_service.extract_invoice_data = AsyncMock(return_value={})
        
        # Mock del DocumentProcessor para evitar problemas con coroutines
        from unittest.mock import patch, Mock, AsyncMock as AsyncMockPatch
        with patch('app.application.use_cases.document_upload_use_cases.DocumentProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor.classify_document = AsyncMockPatch(return_value={
                "classification": "FACTURA",
                "processing_time_ms": 500,
                "analysis_result": analysis_result
            })
            mock_processor.extract_data = AsyncMockPatch(return_value={})
            mock_processor.register_events = AsyncMockPatch()
            mock_processor_class.return_value = mock_processor
            
            mock_document_repository.save_document = AsyncMock(return_value=Document(
                id=1,
                filename="test_1234567890.pdf",
                original_filename="test.pdf",
                file_type="PDF",
                classification="FACTURA",
                s3_key=s3_key_returned,  # Incluir s3_key en el documento retornado
                s3_bucket="test-bucket",
                uploaded_by=1
            ))
            
            use_case = DocumentUploadUseCases(
                s3_service=mock_s3_service,
                document_repository=mock_document_repository,
                textract_service=mock_textract_service
            )
            
            result = await use_case.upload_document(
                file=sample_pdf_file,
                user_id=1
            )
            
            assert result["s3_key"] is not None
            assert result["s3_key"] == s3_key_returned
            mock_s3_service.upload_file.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.document_upload
    async def test_upload_continues_if_s3_fails(self, sample_pdf_file, mock_s3_service, mock_document_repository, mock_textract_service):
        """Test 10: Debe continuar si S3 falla."""
        mock_s3_service.upload_file = AsyncMock(return_value=None)
        
        mock_document_repository.save_document = AsyncMock(return_value=Document(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_type="PDF",
            uploaded_by=1
        ))
        
        use_case = DocumentUploadUseCases(
            s3_service=mock_s3_service,
            document_repository=mock_document_repository,
            textract_service=mock_textract_service
        )
        
        result = await use_case.upload_document(
            file=sample_pdf_file,
            user_id=1
        )
        
        assert result["success"] is True
        assert result["s3_key"] is None
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.document_upload
    async def test_upload_saves_to_database(self, sample_pdf_file, mock_s3_service, mock_document_repository, mock_textract_service):
        """Test 11: Debe guardar en base de datos."""
        mock_document_repository.save_document = AsyncMock(return_value=Document(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_type="PDF",
            uploaded_by=1
        ))
        
        use_case = DocumentUploadUseCases(
            s3_service=mock_s3_service,
            document_repository=mock_document_repository,
            textract_service=mock_textract_service
        )
        
        result = await use_case.upload_document(
            file=sample_pdf_file,
            user_id=1
        )
        
        mock_document_repository.save_document.assert_called_once()
        assert result["document_id"] == 1
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.document_upload
    async def test_upload_registers_events(self, sample_pdf_file, mock_s3_service, mock_document_repository, mock_textract_service):
        """Test 12: Debe registrar eventos."""
        mock_document_repository.save_document = AsyncMock(return_value=Document(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_type="PDF",
            classification="FACTURA",
            uploaded_by=1
        ))
        
        use_case = DocumentUploadUseCases(
            s3_service=mock_s3_service,
            document_repository=mock_document_repository,
            textract_service=mock_textract_service
        )
        
        await use_case.upload_document(
            file=sample_pdf_file,
            user_id=1
        )
        
        # Verificar que se llamó save_event
        assert mock_document_repository.save_event.called
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.document_upload
    async def test_upload_includes_processing_time(self, sample_pdf_file, mock_s3_service, mock_document_repository, mock_textract_service):
        """Test 13: Debe incluir tiempo de procesamiento."""
        mock_textract_service.analyze_document = AsyncMock(return_value={
            "classification": "FACTURA",
            "raw_text": "Invoice text",
            "confidence": 95.0,
            "processing_time_ms": 500
        })
        
        mock_document_repository.save_document = AsyncMock(return_value=Document(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_type="PDF",
            classification="FACTURA",
            uploaded_by=1
        ))
        
        use_case = DocumentUploadUseCases(
            s3_service=mock_s3_service,
            document_repository=mock_document_repository,
            textract_service=mock_textract_service
        )
        
        result = await use_case.upload_document(
            file=sample_pdf_file,
            user_id=1
        )
        
        assert "processing_time_ms" in result
        assert result["processing_time_ms"] == 500
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.document_upload
    async def test_upload_handles_textract_error(self, sample_pdf_file, mock_s3_service, mock_document_repository, mock_textract_service):
        """Test 14: Debe manejar errores de Textract."""
        mock_textract_service.analyze_document = AsyncMock(side_effect=Exception("Textract error"))
        
        mock_document_repository.save_document = AsyncMock(return_value=Document(
            id=1,
            filename="test.pdf",
            original_filename="test.pdf",
            file_type="PDF",
            uploaded_by=1
        ))
        
        use_case = DocumentUploadUseCases(
            s3_service=mock_s3_service,
            document_repository=mock_document_repository,
            textract_service=mock_textract_service
        )
        
        # Debe continuar aunque Textract falle
        result = await use_case.upload_document(
            file=sample_pdf_file,
            user_id=1
        )
        
        assert result["success"] is True
        assert result["classification"] is None or result["classification"] == "INFORMACIÓN"

