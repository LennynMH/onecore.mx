"""Authentication repository implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.domain.repositories.auth_repository import AuthRepository
from app.infrastructure.database.sql_server import SQLServerService

logger = logging.getLogger(__name__)


class AuthRepositoryImpl(AuthRepository):
    """Implementation of authentication repository."""
    
    def __init__(self, db_service: SQLServerService):
        """Initialize repository with database service."""
        self.db_service = db_service
    
    async def create_or_get_anonymous_session(self, rol: str = "gestor") -> Dict[str, Any]:
        """
        Create a new anonymous session or get an existing inactive one.
        
        Args:
            rol: Role name to assign to the session (default: "gestor")
            
        Returns:
            Dictionary with session data
        """
        conn = None
        cursor = None
        try:
            conn = self.db_service.get_connection()
            cursor = conn.cursor()
            
            # First, get or validate the role ID
            cursor.execute("""
                SELECT id, nombre FROM roles WHERE nombre = ?
            """, (rol,))
            
            role_row = cursor.fetchone()
            
            if not role_row:
                # Role doesn't exist, use default "gestor"
                logger.warning(f"Role '{rol}' not found, using default 'gestor'")
                cursor.execute("""
                    SELECT id, nombre FROM roles WHERE nombre = 'gestor'
                """)
                role_row = cursor.fetchone()
                
                if not role_row:
                    raise Exception("Default role 'gestor' not found in database")
            
            rol_id = role_row[0]
            rol_nombre = role_row[1]
            
            # Try to get an inactive session first
            cursor.execute("""
                SELECT TOP 1 s.id, s.session_id, s.created_at, r.nombre
                FROM anonymous_sessions s
                INNER JOIN roles r ON s.rol_id = r.id
                WHERE s.is_active = 0 AND s.rol_id = ?
                ORDER BY s.created_at ASC
            """, (rol_id,))
            
            row = cursor.fetchone()
            
            if row:
                # Reuse existing inactive session
                session_id = row[0]
                session_uuid = row[1]
                created_at = row[2]
                session_rol = row[3]
                
                # Activate and update activity
                cursor.execute("""
                    UPDATE anonymous_sessions
                    SET is_active = 1,
                        last_activity = GETDATE()
                    WHERE id = ?
                """, (session_id,))
                
                conn.commit()
                
                logger.info(f"Reused anonymous session ID: {session_id} with role: {session_rol}")
                
                return {
                    "id": session_id,
                    "session_id": str(session_uuid),
                    "rol": session_rol,
                    "created_at": created_at.isoformat() if created_at else None
                }
            else:
                # Create new session with the specified role
                cursor.execute("""
                    INSERT INTO anonymous_sessions (rol_id, created_at, last_activity, is_active)
                    OUTPUT INSERTED.id, INSERTED.session_id, INSERTED.created_at
                    VALUES (?, GETDATE(), GETDATE(), 1)
                """, (rol_id,))
                
                row = cursor.fetchone()
                conn.commit()
                
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
            if conn:
                conn.rollback()
            logger.error(f"Error creating/getting anonymous session: {str(e)}")
            raise Exception(f"Failed to create/get anonymous session: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    async def update_session_activity(self, session_id: int) -> bool:
        """
        Update last activity timestamp for a session.
        
        Args:
            session_id: Session ID to update
            
        Returns:
            True if successful
        """
        conn = None
        cursor = None
        try:
            conn = self.db_service.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE anonymous_sessions
                SET last_activity = GETDATE()
                WHERE id = ?
            """, (session_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error updating session activity: {str(e)}")
            return False
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

