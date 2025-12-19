"""
SQLAlchemy models for database tables.

Refactorización con Auto (Claude/ChatGPT) - Migración a SQLAlchemy ORM

¿Qué hace este módulo?
Define todos los modelos SQLAlchemy que representan las tablas de la base de datos.
Estos modelos permiten usar SQLAlchemy ORM en lugar de queries SQL directas.

¿Qué clases contiene?
- Role: Modelo para tabla roles
- AnonymousSession: Modelo para tabla anonymous_sessions
- FileUpload: Modelo para tabla file_uploads
- FileData: Modelo para tabla file_data
- FileValidationError: Modelo para tabla file_validation_errors
- Document: Modelo para tabla documents
- DocumentExtractedData: Modelo para tabla document_extracted_data
- LogEvent: Modelo para tabla log_events
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Boolean, BigInteger,
    Text, Index
)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Role(Base):
    """
    Modelo para la tabla roles.
    
    ¿Qué hace la clase?
    Representa un rol del sistema (admin, gestor) con su descripción.
    
    ¿Qué campos tiene?
    - id: ID único del rol
    - nombre: Nombre del rol (único)
    - descripcion: Descripción del rol
    - created_at: Fecha de creación
    """
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(50), nullable=False, unique=True)
    descripcion = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    anonymous_sessions = relationship("AnonymousSession", back_populates="role")


class AnonymousSession(Base):
    """
    Modelo para la tabla anonymous_sessions.
    
    ¿Qué hace la clase?
    Representa una sesión de usuario anónimo con su rol asignado.
    
    ¿Qué campos tiene?
    - id: ID único de la sesión
    - session_id: UUID único de la sesión
    - created_at: Fecha de creación
    - last_activity: Fecha de última actividad
    - rol_id: ID del rol asignado (FK a roles)
    - is_active: Indica si la sesión está activa
    """
    __tablename__ = "anonymous_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UNIQUEIDENTIFIER, default=None, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    rol_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relaciones
    role = relationship("Role", back_populates="anonymous_sessions")
    documents = relationship("Document", back_populates="uploaded_by_user")
    log_events = relationship("LogEvent", back_populates="user")


class FileUpload(Base):
    """
    Modelo para la tabla file_uploads.
    
    ¿Qué hace la clase?
    Representa los metadatos de un archivo CSV subido al sistema.
    
    ¿Qué campos tiene?
    - id: ID único del archivo
    - filename: Nombre del archivo con timestamp
    - s3_key: Clave S3 del archivo
    - s3_bucket: Bucket S3
    - uploaded_by: ID del usuario que subió el archivo
    - uploaded_at: Fecha de subida
    - row_count: Número de filas procesadas
    - has_errors: Indica si el archivo tiene errores
    - error_count: Número total de errores
    - created_at: Fecha de creación del registro
    """
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    s3_key = Column(String(500), nullable=True)
    s3_bucket = Column(String(255), nullable=True)
    uploaded_by = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, nullable=False)
    row_count = Column(Integer, nullable=True)
    has_errors = Column(Boolean, default=False, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    file_data_rows = relationship("FileData", back_populates="file_upload", cascade="all, delete-orphan")
    validation_errors = relationship("FileValidationError", back_populates="file_upload", cascade="all, delete-orphan")
    
    # Índices
    __table_args__ = (
        Index("idx_file_uploads_uploaded_by", "uploaded_by"),
        Index("idx_file_uploads_uploaded_at", "uploaded_at"),
        Index("idx_file_uploads_filename", "filename"),
        Index("idx_file_uploads_has_errors", "has_errors"),
    )


class FileData(Base):
    """
    Modelo para la tabla file_data.
    
    ¿Qué hace la clase?
    Representa una fila de datos de un archivo CSV almacenada como JSON.
    
    ¿Qué campos tiene?
    - id: ID único de la fila
    - file_id: ID del archivo al que pertenece (FK a file_uploads)
    - row_data: Datos de la fila en formato JSON
    - created_at: Fecha de creación
    """
    __tablename__ = "file_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey("file_uploads.id", ondelete="CASCADE"), nullable=False)
    row_data = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    file_upload = relationship("FileUpload", back_populates="file_data_rows")
    
    # Índices
    __table_args__ = (
        Index("idx_file_data_file_id", "file_id"),
        Index("idx_file_data_created_at", "created_at"),
    )


class FileValidationError(Base):
    """
    Modelo para la tabla file_validation_errors.
    
    ¿Qué hace la clase?
    Representa un error de validación encontrado en un archivo CSV.
    
    ¿Qué campos tiene?
    - id: ID único del error
    - file_id: ID del archivo con el error (FK a file_uploads)
    - error_type: Tipo de error (empty_value, type_error, duplicate, etc.)
    - field_name: Nombre del campo con error
    - error_message: Mensaje descriptivo del error
    - row_number: Número de fila donde ocurrió el error
    - created_at: Fecha de creación del registro
    """
    __tablename__ = "file_validation_errors"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey("file_uploads.id", ondelete="CASCADE"), nullable=False)
    error_type = Column(String(50), nullable=False)
    field_name = Column(String(255), nullable=True)
    error_message = Column(String(500), nullable=False)
    row_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    file_upload = relationship("FileUpload", back_populates="validation_errors")
    
    # Índices
    __table_args__ = (
        Index("idx_file_validation_errors_file_id", "file_id"),
        Index("idx_file_validation_errors_type", "error_type"),
    )


class Document(Base):
    """
    Modelo para la tabla documents.
    
    ¿Qué hace la clase?
    Representa un documento (PDF, JPG, PNG) subido al sistema.
    
    ¿Qué campos tiene?
    - id: ID único del documento
    - filename: Nombre del archivo con timestamp
    - original_filename: Nombre original del archivo
    - file_type: Tipo de archivo (PDF, JPG, PNG)
    - s3_key: Clave S3 del documento
    - s3_bucket: Bucket S3
    - classification: Clasificación del documento (FACTURA, INFORMACIÓN)
    - uploaded_by: ID del usuario que subió el documento (FK a anonymous_sessions)
    - uploaded_at: Fecha de subida
    - processed_at: Fecha de procesamiento
    - file_size: Tamaño del archivo en bytes
    """
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    s3_key = Column(String(500), nullable=True)
    s3_bucket = Column(String(255), nullable=True)
    classification = Column(String(50), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("anonymous_sessions.id", ondelete="CASCADE"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    file_size = Column(BigInteger, nullable=True)
    
    # Relaciones
    uploaded_by_user = relationship("AnonymousSession", back_populates="documents")
    extracted_data = relationship("DocumentExtractedData", back_populates="document", cascade="all, delete-orphan")
    log_events = relationship("LogEvent", back_populates="document")
    
    # Índices
    __table_args__ = (
        Index("idx_documents_uploaded_by", "uploaded_by"),
        Index("idx_documents_classification", "classification"),
        Index("idx_documents_uploaded_at", "uploaded_at"),
        Index("idx_documents_file_type", "file_type"),
    )


class DocumentExtractedData(Base):
    """
    Modelo para la tabla document_extracted_data.
    
    ¿Qué hace la clase?
    Representa los datos extraídos de un documento (factura o información).
    
    ¿Qué campos tiene?
    - id: ID único de los datos extraídos
    - document_id: ID del documento (FK a documents)
    - data_type: Tipo de datos (INVOICE, INFORMATION)
    - extracted_data: Datos extraídos en formato JSON
    - created_at: Fecha de creación
    """
    __tablename__ = "document_extracted_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    data_type = Column(String(50), nullable=False)
    extracted_data = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    document = relationship("Document", back_populates="extracted_data")
    
    # Índices
    __table_args__ = (
        Index("idx_document_extracted_data_document_id", "document_id"),
        Index("idx_document_extracted_data_data_type", "data_type"),
    )


class LogEvent(Base):
    """
    Modelo para la tabla log_events.
    
    ¿Qué hace la clase?
    Representa un evento registrado en el sistema (carga de documento, procesamiento IA, etc.).
    
    ¿Qué campos tiene?
    - id: ID único del evento
    - event_type: Tipo de evento (DOCUMENT_UPLOAD, AI_PROCESSING, USER_INTERACTION)
    - description: Descripción del evento
    - document_id: ID del documento relacionado (FK a documents, nullable)
    - user_id: ID del usuario relacionado (FK a anonymous_sessions, nullable)
    - created_at: Fecha de creación del evento
    """
    __tablename__ = "log_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(Integer, ForeignKey("anonymous_sessions.id", ondelete="NO ACTION"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relaciones
    document = relationship("Document", back_populates="log_events")
    user = relationship("AnonymousSession", back_populates="log_events")
    
    # Índices
    __table_args__ = (
        Index("idx_log_events_type", "event_type"),
        Index("idx_log_events_created_at", "created_at"),
        Index("idx_log_events_document_id", "document_id"),
        Index("idx_log_events_user_id", "user_id"),
    )

