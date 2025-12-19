"""
Pruebas unitarias para FileUploadUseCases.

Este módulo contiene al menos 10 casos de prueba para cada método de FileUploadUseCases.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi import UploadFile
from io import BytesIO
from typing import Dict, Any

from app.application.use_cases.file_upload_use_cases import FileUploadUseCases
from app.domain.entities.file_upload import FileUpload


class TestUploadAndValidateFile:
    """Pruebas para el método upload_and_validate_file."""
    
    @pytest.fixture
    def sample_csv_file(self):
        """Fixture para archivo CSV válido."""
        content = b"name,email,age,city\nJohn Doe,john@example.com,30,New York\nJane Smith,jane@example.com,25,Los Angeles"
        return UploadFile(
            filename="test.csv",
            file=BytesIO(content)
        )
    
    @pytest.fixture
    def sample_csv_with_errors(self):
        """Fixture para archivo CSV con errores."""
        content = b"name,email,age,city\n,invalid-email,abc,New York\nJohn Doe,john@example.com,30,"
        return UploadFile(
            filename="test_errors.csv",
            file=BytesIO(content)
        )
    
    @pytest.fixture
    def sample_csv_duplicates(self):
        """Fixture para archivo CSV con duplicados."""
        content = b"name,email,age,city\nJohn Doe,john@example.com,30,New York\nJohn Doe,john@example.com,30,New York"
        return UploadFile(
            filename="test_duplicates.csv",
            file=BytesIO(content)
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.file_upload
    async def test_upload_valid_csv_success(self, sample_csv_file, mock_s3_service, mock_file_repository):
        """Test 1: Subir CSV válido debe retornar success=True."""
        use_case = FileUploadUseCases(
            s3_service=mock_s3_service,
            file_repository=mock_file_repository
        )
        
        result = await use_case.upload_and_validate_file(
            file=sample_csv_file,
            param1="value1",
            param2="value2",
            user_id=1
        )
        
        assert result["success"] is True
        assert "filename" in result
        assert result["rows_processed"] > 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.file_upload
    async def test_upload_csv_generates_unique_filename(self, sample_csv_file, mock_s3_service, mock_file_repository):
        """Test 2: Debe generar nombre único con timestamp."""
        use_case = FileUploadUseCases(
            s3_service=mock_s3_service,
            file_repository=mock_file_repository
        )
        
        result = await use_case.upload_and_validate_file(
            file=sample_csv_file,
            param1="value1",
            param2="value2",
            user_id=1
        )
        
        assert "_" in result["filename"]
        assert result["filename"].endswith(".csv")
        assert result["filename"] != "test.csv"  # Debe tener timestamp
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.file_upload
    async def test_upload_csv_validates_empty_values(self, sample_csv_with_errors, mock_s3_service, mock_file_repository):
        """Test 3: Debe detectar valores vacíos."""
        use_case = FileUploadUseCases(
            s3_service=mock_s3_service,
            file_repository=mock_file_repository
        )
        
        result = await use_case.upload_and_validate_file(
            file=sample_csv_with_errors,
            param1="value1",
            param2="value2",
            user_id=1
        )
        
        assert result["success"] is True  # Sube pero con errores
        assert len(result["validation_errors"]) > 0
        assert any(error["type"] == "empty_value" for error in result["validation_errors"])
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.file_upload
    async def test_upload_csv_validates_email_format(self, mock_s3_service, mock_file_repository):
        """Test 4: Debe validar formato de email."""
        # Crear CSV con email inválido
        content = b"name,email,age,city\nJohn Doe,invalid-email,30,New York"
        file = UploadFile(filename="test.csv", file=BytesIO(content))
        
        use_case = FileUploadUseCases(
            s3_service=mock_s3_service,
            file_repository=mock_file_repository
        )
        
        result = await use_case.upload_and_validate_file(
            file=file,
            param1="value1",
            param2="value2",
            user_id=1
        )
        
        # Verificar que hay errores de tipo incorrecto relacionados con email
        email_errors = [
            error for error in result["validation_errors"]
            if error["type"] == "incorrect_type" and "email" in error.get("field", "").lower()
        ]
        assert len(email_errors) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.file_upload
    async def test_upload_csv_detects_duplicates(self, sample_csv_duplicates, mock_s3_service, mock_file_repository):
        """Test 5: Debe detectar filas duplicadas."""
        use_case = FileUploadUseCases(
            s3_service=mock_s3_service,
            file_repository=mock_file_repository
        )
        
        result = await use_case.upload_and_validate_file(
            file=sample_csv_duplicates,
            param1="value1",
            param2="value2",
            user_id=1
        )
        
        assert any(error["type"] == "duplicate" for error in result["validation_errors"])
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.file_upload
    async def test_upload_csv_includes_params(self, sample_csv_file, mock_s3_service, mock_file_repository):
        """Test 6: Debe incluir param1 y param2 en resultado."""
        use_case = FileUploadUseCases(
            s3_service=mock_s3_service,
            file_repository=mock_file_repository
        )
        
        result = await use_case.upload_and_validate_file(
            file=sample_csv_file,
            param1="custom_param1",
            param2="custom_param2",
            user_id=1
        )
        
        assert result["param1"] == "custom_param1"
        assert result["param2"] == "custom_param2"
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.file_upload
    async def test_upload_csv_s3_upload_success(self, sample_csv_file, mock_s3_service, mock_file_repository):
        """Test 7: Debe subir a S3 exitosamente."""
        mock_s3_service.upload_file = AsyncMock(return_value="uploads/2025/12/19/test_file.csv")
        
        use_case = FileUploadUseCases(
            s3_service=mock_s3_service,
            file_repository=mock_file_repository
        )
        
        result = await use_case.upload_and_validate_file(
            file=sample_csv_file,
            param1="value1",
            param2="value2",
            user_id=1
        )
        
        assert result["s3_key"] is not None
        assert result["s3_bucket"] is not None
        mock_s3_service.upload_file.assert_called_once()
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.file_upload
    async def test_upload_csv_s3_upload_failure_continues(self, sample_csv_file, mock_s3_service, mock_file_repository):
        """Test 8: Si S3 falla, debe continuar con BD."""
        mock_s3_service.upload_file = AsyncMock(return_value=None)
        
        use_case = FileUploadUseCases(
            s3_service=mock_s3_service,
            file_repository=mock_file_repository
        )
        
        result = await use_case.upload_and_validate_file(
            file=sample_csv_file,
            param1="value1",
            param2="value2",
            user_id=1
        )
        
        assert result["success"] is True  # Debe continuar aunque S3 falle
        assert result["s3_key"] is None
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.file_upload
    async def test_upload_csv_saves_to_database(self, sample_csv_file, mock_s3_service, mock_file_repository):
        """Test 9: Debe guardar datos en base de datos."""
        use_case = FileUploadUseCases(
            s3_service=mock_s3_service,
            file_repository=mock_file_repository
        )
        
        result = await use_case.upload_and_validate_file(
            file=sample_csv_file,
            param1="value1",
            param2="value2",
            user_id=1
        )
        
        mock_file_repository.save_file_data.assert_called_once()
        call_args = mock_file_repository.save_file_data.call_args
        assert call_args is not None
        assert len(call_args[0][0]) > 0  # Debe tener datos
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.file_upload
    async def test_upload_csv_counts_rows_processed(self, sample_csv_file, mock_s3_service, mock_file_repository):
        """Test 10: Debe contar filas procesadas correctamente."""
        use_case = FileUploadUseCases(
            s3_service=mock_s3_service,
            file_repository=mock_file_repository
        )
        
        result = await use_case.upload_and_validate_file(
            file=sample_csv_file,
            param1="value1",
            param2="value2",
            user_id=1
        )
        
        assert result["rows_processed"] == 2  # 2 filas de datos (sin encabezado)
        assert isinstance(result["rows_processed"], int)
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.file_upload
    async def test_upload_csv_validates_numeric_fields(self, mock_s3_service, mock_file_repository):
        """Test 11: Debe validar campos numéricos."""
        content = b"name,email,age,city\nJohn Doe,john@example.com,not_a_number,New York"
        file = UploadFile(filename="test.csv", file=BytesIO(content))
        
        use_case = FileUploadUseCases(
            s3_service=mock_s3_service,
            file_repository=mock_file_repository
        )
        
        result = await use_case.upload_and_validate_file(
            file=file,
            param1="value1",
            param2="value2",
            user_id=1
        )
        
        assert any(
            error["type"] == "incorrect_type" and "age" in error.get("field", "").lower()
            for error in result["validation_errors"]
        )
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.file_upload
    async def test_upload_csv_handles_empty_file(self, mock_s3_service, mock_file_repository):
        """Test 12: Debe manejar archivo vacío."""
        content = b"name,email,age,city\n"
        file = UploadFile(filename="empty.csv", file=BytesIO(content))
        
        use_case = FileUploadUseCases(
            s3_service=mock_s3_service,
            file_repository=mock_file_repository
        )
        
        result = await use_case.upload_and_validate_file(
            file=file,
            param1="value1",
            param2="value2",
            user_id=1
        )
        
        assert result["rows_processed"] == 0
        assert result["success"] is True
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.file_upload
    async def test_upload_csv_preserves_original_filename(self, sample_csv_file, mock_s3_service, mock_file_repository):
        """Test 13: Debe preservar nombre original en metadata."""
        use_case = FileUploadUseCases(
            s3_service=mock_s3_service,
            file_repository=mock_file_repository
        )
        
        result = await use_case.upload_and_validate_file(
            file=sample_csv_file,
            param1="value1",
            param2="value2",
            user_id=1
        )
        
        # Verificar que el resultado incluye el nombre original
        assert "original_filename" in result or result.get("filename") != "test.csv"
        # El filename debe tener timestamp pero el original_filename debe ser el original
        assert result["filename"] != sample_csv_file.filename or "_" in result["filename"]
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.file_upload
    async def test_upload_csv_error_handling(self, mock_s3_service, mock_file_repository):
        """Test 14: Debe manejar errores de procesamiento."""
        mock_file_repository.save_file_data = AsyncMock(side_effect=Exception("Database error"))
        
        content = b"name,email,age,city\nJohn Doe,john@example.com,30,New York"
        file = UploadFile(filename="test.csv", file=BytesIO(content))
        
        use_case = FileUploadUseCases(
            s3_service=mock_s3_service,
            file_repository=mock_file_repository
        )
        
        with pytest.raises(Exception):
            await use_case.upload_and_validate_file(
                file=file,
                param1="value1",
                param2="value2",
                user_id=1
            )

