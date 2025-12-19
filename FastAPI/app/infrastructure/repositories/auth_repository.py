"""
Authentication repository implementation.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.1

¿Qué hace este módulo?
Implementa el repositorio de autenticación usando SQL Server.
Esta refactorización utiliza DatabaseHelper para eliminar código duplicado
de manejo de conexiones y transacciones.

¿Qué clases contiene?
- AuthRepositoryImpl: Implementación del repositorio de autenticación
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.domain.repositories.auth_repository import AuthRepository
from app.infrastructure.database.sql_server import SQLServerService
from app.infrastructure.database.db_helper import DatabaseHelper

logger = logging.getLogger(__name__)


class AuthRepositoryImpl(AuthRepository):
    """
    Implementación del repositorio de autenticación.
    
    ¿Qué hace la clase?
    Proporciona métodos para crear y gestionar sesiones anónimas,
    incluyendo reutilización de sesiones inactivas y actualización de actividad.
    """
    
    def __init__(self, db_service: SQLServerService):
        """
        Inicializa el repositorio con el servicio de base de datos.
        
        ¿Qué hace la función?
        Configura el repositorio con el servicio de base de datos y crea
        un helper para operaciones comunes.
        
        ¿Qué parámetros recibe y de qué tipo?
        - db_service (SQLServerService): Servicio de base de datos SQL Server
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
        self.db_service = db_service
        self.db_helper = DatabaseHelper(db_service)
    
    async def create_or_get_anonymous_session(self, rol: str = "gestor") -> Dict[str, Any]:
        """
        Crea una nueva sesión anónima o reutiliza una existente inactiva.
        
        ¿Qué hace la función?
        Busca primero una sesión inactiva del rol especificado para reutilizarla.
        Si no encuentra ninguna, crea una nueva sesión con el rol indicado.
        Si el rol no existe, usa el rol por defecto "gestor".
        
        ¿Qué parámetros recibe y de qué tipo?
        - rol (str): Nombre del rol a asignar a la sesión (default: "gestor")
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con datos de la sesión:
          - id: ID de la sesión
          - session_id: UUID de la sesión
          - rol: Nombre del rol asignado
          - created_at: Fecha de creación en formato ISO
        """
        try:
            with self.db_helper.get_connection() as (conn, cursor):
                # Primero, obtener o validar el ID del rol
                cursor.execute("""
                    SELECT id, nombre FROM roles WHERE nombre = ?
                """, (rol,))
                
                role_row = cursor.fetchone()
                
                if not role_row:
                    # El rol no existe, usar "gestor" por defecto
                    logger.warning(f"Role '{rol}' not found, using default 'gestor'")
                    cursor.execute("""
                        SELECT id, nombre FROM roles WHERE nombre = 'gestor'
                    """)
                    role_row = cursor.fetchone()
                    
                    if not role_row:
                        raise Exception("Default role 'gestor' not found in database")
                
                rol_id = role_row[0]
                rol_nombre = role_row[1]
                
                # Intentar obtener una sesión inactiva primero
                cursor.execute("""
                    SELECT TOP 1 s.id, s.session_id, s.created_at, r.nombre
                    FROM anonymous_sessions s
                    INNER JOIN roles r ON s.rol_id = r.id
                    WHERE s.is_active = 0 AND s.rol_id = ?
                    ORDER BY s.created_at ASC
                """, (rol_id,))
                
                row = cursor.fetchone()
                
                if row:
                    # Reutilizar sesión inactiva existente
                    session_id = row[0]
                    session_uuid = row[1]
                    created_at = row[2]
                    session_rol = row[3]
                    
                    # Activar y actualizar actividad
                    cursor.execute("""
                        UPDATE anonymous_sessions
                        SET is_active = 1,
                            last_activity = GETDATE()
                        WHERE id = ?
                    """, (session_id,))
                    
                    logger.info(f"Reused anonymous session ID: {session_id} with role: {session_rol}")
                    
                    return {
                        "id": session_id,
                        "session_id": str(session_uuid),
                        "rol": session_rol,
                        "created_at": created_at.isoformat() if created_at else None
                    }
                else:
                    # Crear nueva sesión con el rol especificado
                    cursor.execute("""
                        INSERT INTO anonymous_sessions (rol_id, created_at, last_activity, is_active)
                        OUTPUT INSERTED.id, INSERTED.session_id, INSERTED.created_at
                        VALUES (?, GETDATE(), GETDATE(), 1)
                    """, (rol_id,))
                    
                    row = cursor.fetchone()
                    
                    session_id = row[0]
                    session_uuid = row[1]
                    created_at = row[2]
                    
                    logger.info(f"Created new anonymous session ID: {session_id} with role: {rol_nombre}")
                    
                    return {
                        "id": session_id,
                        "session_id": str(session_uuid),
                        "rol": rol_nombre,
                        "created_at": created_at.isoformat() if created_at else None
                    }
        except Exception as e:
            logger.error(f"Error creating/getting anonymous session: {str(e)}")
            raise Exception(f"Failed to create/get anonymous session: {str(e)}")
    
    async def update_session_activity(self, session_id: int) -> bool:
        """
        Actualiza el timestamp de última actividad de una sesión.
        
        ¿Qué hace la función?
        Actualiza el campo `last_activity` de una sesión anónima con la fecha
        y hora actual, indicando que la sesión sigue activa.
        
        ¿Qué parámetros recibe y de qué tipo?
        - session_id (int): ID de la sesión a actualizar
        
        ¿Qué dato regresa y de qué tipo?
        - bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            with self.db_helper.get_connection() as (conn, cursor):
                cursor.execute("""
                    UPDATE anonymous_sessions
                    SET last_activity = GETDATE()
                    WHERE id = ?
                """, (session_id,))
                return True
        except Exception as e:
            logger.error(f"Error updating session activity: {str(e)}")
            return False

