"""
SQLAlchemy database configuration.

Refactorización con Auto (Claude/ChatGPT) - Migración a SQLAlchemy ORM

¿Qué hace este módulo?
Configura el engine y la sesión de SQLAlchemy para conectarse a SQL Server.
Proporciona funciones para obtener sesiones de base de datos de forma segura.

¿Qué funciones contiene?
- get_engine: Crea y retorna el engine de SQLAlchemy
- get_session: Context manager para obtener sesiones de base de datos
- get_db: Dependency para FastAPI que proporciona sesiones
"""

import logging
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from sqlalchemy.dialects.mssql import pyodbc

from app.core.config import settings
from app.infrastructure.database.models import Base

logger = logging.getLogger(__name__)

# Engine global
_engine = None
_SessionLocal = None


def get_engine():
    """
    Obtiene o crea el engine de SQLAlchemy.
    
    ¿Qué hace la función?
    Crea un engine de SQLAlchemy para conectarse a SQL Server usando pyodbc.
    El engine se crea una sola vez y se reutiliza en llamadas posteriores.
    
    ¿Qué parámetros recibe y de qué tipo?
    - None
    
    ¿Qué dato regresa y de qué tipo?
    - Engine: Engine de SQLAlchemy configurado para SQL Server
    """
    global _engine
    
    if _engine is None:
        # Construir connection string para SQLAlchemy
        connection_string = (
            f"mssql+pyodbc://{settings.sql_server_user}:{settings.sql_server_password}"
            f"@{settings.sql_server_host}:{settings.sql_server_port}/{settings.sql_server_database}"
            f"?driver={settings.sql_server_driver.replace(' ', '+')}"
            "&TrustServerCertificate=yes"
        )
        
        # Crear engine con configuración optimizada para SQL Server
        _engine = create_engine(
            connection_string,
            poolclass=NullPool,  # No usar pool para compatibilidad con pyodbc
            echo=False,  # Cambiar a True para ver queries SQL en logs
            future=True,
            connect_args={
                "timeout": 30,
                "autocommit": False,
            }
        )
        
        # Configurar eventos para logging (opcional)
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            """Configuración adicional al conectar."""
            pass
        
        logger.info("SQLAlchemy engine created successfully")
    
    return _engine


def get_session_local():
    """
    Obtiene o crea la clase SessionLocal.
    
    ¿Qué hace la función?
    Crea una clase SessionLocal para generar sesiones de base de datos.
    La clase se crea una sola vez y se reutiliza.
    
    ¿Qué parámetros recibe y de qué tipo?
    - None
    
    ¿Qué dato regresa y de qué tipo?
    - sessionmaker: Clase para crear sesiones de base de datos
    """
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
            class_=Session,
            future=True
        )
        logger.info("SQLAlchemy SessionLocal created successfully")
    
    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager para obtener una sesión de base de datos.
    
    ¿Qué hace la función?
    Proporciona una sesión de SQLAlchemy dentro de un context manager,
    asegurando que se haga commit o rollback automáticamente y que la
    sesión se cierre correctamente.
    
    ¿Qué parámetros recibe y de qué tipo?
    - None
    
    ¿Qué dato regresa y de qué tipo?
    - Generator[Session, None, None]: Generador que produce una sesión de base de datos
    
    Ejemplo de uso:
    ```python
    with get_session() as session:
        # Usar session aquí
        user = session.query(User).first()
        session.commit()
    ```
    """
    SessionLocal = get_session_local()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para FastAPI que proporciona sesiones de base de datos.
    
    ¿Qué hace la función?
    Generador que proporciona una sesión de SQLAlchemy para usar en endpoints de FastAPI.
    La sesión se cierra automáticamente después de que el endpoint termine.
    
    ¿Qué parámetros recibe y de qué tipo?
    - None
    
    ¿Qué dato regresa y de qué tipo?
    - Generator[Session, None, None]: Generador que produce una sesión de base de datos
    
    Ejemplo de uso en FastAPI:
    ```python
    @router.get("/items")
    def get_items(db: Session = Depends(get_db)):
        items = db.query(Item).all()
        return items
    ```
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicializa las tablas en la base de datos.
    
    ¿Qué hace la función?
    Crea todas las tablas definidas en los modelos SQLAlchemy si no existen.
    Esta función se puede usar para inicializar la base de datos en desarrollo.
    
    ¿Qué parámetros recibe y de qué tipo?
    - None
    
    ¿Qué dato regresa y de qué tipo?
    - None
    
    Nota: En producción, las tablas deben crearse usando migraciones o scripts SQL.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized")

