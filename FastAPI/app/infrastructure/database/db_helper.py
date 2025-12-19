"""
Database Helper - Helper para operaciones comunes de base de datos.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.1

¿Qué hace este módulo?
Proporciona un context manager y funciones helper para manejar conexiones de base de datos,
transacciones, y operaciones comunes, eliminando código duplicado en los repositorios.

¿Qué clases contiene?
- DatabaseHelper: Context manager para operaciones de base de datos
"""

import logging
from contextlib import contextmanager
from typing import Optional, Callable, Any
from app.infrastructure.database.sql_server import SQLServerService

logger = logging.getLogger(__name__)


class DatabaseHelper:
    """
    Helper para operaciones comunes de base de datos.
    
    ¿Qué hace la clase?
    Proporciona un context manager para manejar conexiones de base de datos de forma
    segura, con manejo automático de transacciones, rollback en errores, y cierre
    de recursos.
    
    ¿Qué métodos tiene?
    - get_connection: Context manager para obtener conexión y cursor
    """
    
    def __init__(self, db_service: SQLServerService):
        """
        Inicializa el helper con el servicio de base de datos.
        
        ¿Qué hace la función?
        Configura el helper con el servicio de base de datos que proporcionará
        las conexiones.
        
        ¿Qué parámetros recibe y de qué tipo?
        - db_service (SQLServerService): Servicio de base de datos SQL Server
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
        self.db_service = db_service
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para obtener conexión y cursor de base de datos.
        
        ¿Qué hace la función?
        Proporciona un context manager que maneja automáticamente la obtención
        de conexión, creación de cursor, manejo de errores con rollback,
        y cierre de recursos en el bloque finally.
        
        ¿Qué parámetros recibe y de qué tipo?
        - Ninguno (context manager)
        
        ¿Qué dato regresa y de qué tipo?
        - Generator[tuple]: Tupla (conn, cursor) que se puede usar en un bloque with
        
        Uso:
        ```python
        with self.db_helper.get_connection() as (conn, cursor):
            cursor.execute("SELECT * FROM table")
            conn.commit()
        ```
        
        Nota: El rollback se maneja automáticamente si ocurre una excepción.
        """
        conn = None
        cursor = None
        try:
            conn = self.db_service.get_connection()
            cursor = conn.cursor()
            yield (conn, cursor)
            # Si llegamos aquí sin excepciones, hacer commit
            if conn:
                conn.commit()
        except Exception as e:
            # Rollback automático en caso de error
            if conn:
                try:
                    conn.rollback()
                except Exception as rollback_error:
                    logger.error(f"Error during rollback: {str(rollback_error)}")
            raise e
        finally:
            # Cerrar recursos
            if cursor:
                try:
                    cursor.close()
                except Exception as close_error:
                    logger.warning(f"Error closing cursor: {str(close_error)}")
            if conn:
                try:
                    conn.close()
                except Exception as close_error:
                    logger.warning(f"Error closing connection: {str(close_error)}")
    
    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = False
    ) -> Any:
        """
        Ejecuta una query y retorna el resultado.
        
        ¿Qué hace la función?
        Ejecuta una query SQL con parámetros opcionales y retorna el resultado
        según el modo especificado (fetch_one, fetch_all, o solo ejecución).
        
        ¿Qué parámetros recibe y de qué tipo?
        - query (str): Query SQL a ejecutar
        - params (Optional[tuple]): Parámetros para la query (default: None)
        - fetch_one (bool): Si True, retorna una sola fila (default: False)
        - fetch_all (bool): Si True, retorna todas las filas (default: False)
        
        ¿Qué dato regresa y de qué tipo?
        - Any: Resultado según el modo:
          - Si fetch_one: Primera fila o None
          - Si fetch_all: Lista de todas las filas
          - Si ninguno: None (solo ejecución)
        """
        with self.get_connection() as (conn, cursor):
            cursor.execute(query, params or ())
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            return None
    
    def execute_transaction(self, operations: list[Callable]) -> bool:
        """
        Ejecuta múltiples operaciones en una transacción.
        
        ¿Qué hace la función?
        Ejecuta una lista de operaciones (callables) dentro de una sola transacción.
        Si alguna operación falla, todas se revierten con rollback.
        
        ¿Qué parámetros recibe y de qué tipo?
        - operations (list[Callable]): Lista de funciones a ejecutar en la transacción
        
        ¿Qué dato regresa y de qué tipo?
        - bool: True si todas las operaciones fueron exitosas, False en caso contrario
        """
        with self.get_connection() as (conn, cursor):
            try:
                for operation in operations:
                    operation(conn, cursor)
                return True
            except Exception as e:
                logger.error(f"Error in transaction: {str(e)}")
                raise

