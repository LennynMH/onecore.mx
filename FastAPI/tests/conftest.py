"""
Configuración global de pytest para OneCore API.

Este archivo contiene fixtures compartidas y configuración para todas las pruebas.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any
from datetime import datetime, timedelta

from app.core.config import Settings
from app.domain.repositories.auth_repository import AuthRepository
from app.domain.repositories.file_repository import FileRepository
from app.domain.repositories.document_repository import DocumentRepository
from app.infrastructure.s3.s3_service import S3Service
from app.infrastructure.ai.textract_service import TextractService
from app.infrastructure.ai.openai_service import OpenAIService


@pytest.fixture
def mock_settings():
    """Fixture para configuración mock."""
    settings = Settings(
        jwt_secret_key="test-secret-key-for-testing-only",
        jwt_expiration_minutes=15,
        jwt_refresh_expiration_minutes=30,
        sql_server_host="localhost",
        sql_server_port=1433,
        sql_server_database="test_db",
        sql_server_user="test_user",
        sql_server_password="test_password",
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        aws_s3_bucket_name="test-bucket",
        openai_api_key="test-openai-key",
        openai_enabled=True
    )
    return settings


@pytest.fixture
def mock_auth_repository():
    """Fixture para repositorio de autenticación mock."""
    repository = Mock(spec=AuthRepository)
    repository.create_or_get_anonymous_session = AsyncMock(
        return_value={
            "id": 1,
            "rol": "gestor",
            "session_id": "test-session-id"
        }
    )
    return repository


@pytest.fixture
def mock_file_repository():
    """Fixture para repositorio de archivos mock."""
    repository = Mock(spec=FileRepository)
    repository.save_file_data = AsyncMock(return_value=True)
    repository.get_file_metadata = AsyncMock(return_value=None)
    return repository


@pytest.fixture
def mock_document_repository():
    """Fixture para repositorio de documentos mock."""
    repository = Mock(spec=DocumentRepository)
    repository.save_document = AsyncMock(return_value=Mock(id=1))
    repository.save_extracted_data = AsyncMock(return_value=True)
    repository.save_event = AsyncMock(return_value=Mock(id=1))
    repository.list_events = AsyncMock(return_value={
        "events": [],
        "total": 0,
        "page": 1,
        "page_size": 50,
        "total_pages": 0
    })
    return repository


@pytest.fixture
def mock_s3_service():
    """Fixture para servicio S3 mock."""
    service = Mock(spec=S3Service)
    service.upload_file = AsyncMock(return_value="s3://test-bucket/test-key")
    service.get_file_url = Mock(return_value="https://test-bucket.s3.amazonaws.com/test-key")
    return service


@pytest.fixture
def mock_textract_service():
    """Fixture para servicio Textract mock."""
    service = Mock(spec=TextractService)
    service.classify_document = AsyncMock(return_value={
        "classification": "FACTURA",
        "confidence": 0.95,
        "text": "Test document text"
    })
    service.extract_invoice_data = AsyncMock(return_value={
        "cliente": {"nombre": "Test Client"},
        "proveedor": {"nombre": "Test Provider"},
        "productos": []
    })
    service.extract_information_data = AsyncMock(return_value={
        "description": "Test description",
        "summary": "Test summary",
        "sentiment": "positive"
    })
    return service


@pytest.fixture
def mock_openai_service():
    """Fixture para servicio OpenAI mock."""
    service = Mock(spec=OpenAIService)
    service.analyze_sentiment = AsyncMock(return_value="positive")
    service.generate_summary = AsyncMock(return_value="Test summary")
    return service


@pytest.fixture
def sample_jwt_token():
    """Fixture para token JWT de prueba."""
    from app.core.security import create_access_token
    data = {
        "id_usuario": 1,
        "rol": "gestor"
    }
    return create_access_token(data, timedelta(minutes=15))


@pytest.fixture
def sample_user_data():
    """Fixture para datos de usuario de prueba."""
    return {
        "id_usuario": 1,
        "rol": "gestor"
    }


@pytest.fixture
def sample_csv_content():
    """Fixture para contenido CSV de prueba."""
    return """name,email,age,city
John Doe,john@example.com,30,New York
Jane Smith,jane@example.com,25,Los Angeles"""


@pytest.fixture
def sample_upload_file():
    """Fixture para archivo de upload mock."""
    from fastapi import UploadFile
    from io import BytesIO
    
    content = b"name,email,age,city\nJohn Doe,john@example.com,30,New York"
    file = UploadFile(
        filename="test.csv",
        file=BytesIO(content)
    )
    return file


@pytest.fixture
def sample_pdf_file():
    """Fixture para archivo PDF mock."""
    from fastapi import UploadFile
    from io import BytesIO
    
    content = b"%PDF-1.4\nTest PDF content"
    file = UploadFile(
        filename="test.pdf",
        file=BytesIO(content)
    )
    return file


@pytest.fixture
def sample_document():
    """Fixture para entidad Document mock."""
    from app.domain.entities.document import Document
    
    return Document(
        id=1,
        filename="test_1234567890.pdf",
        original_filename="test.pdf",
        file_type="PDF",
        classification="FACTURA",
        uploaded_by=1,
        file_size=1024
    )

