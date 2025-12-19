"""
Authentication repository implementation using SQLAlchemy.

Refactorización con Auto (Claude/ChatGPT) - Migración a SQLAlchemy ORM

¿Qué hace este módulo?
Implementa el repositorio de autenticación usando SQLAlchemy ORM en lugar de queries SQL directas.
Mantiene la misma interfaz que la implementación anterior para compatibilidad.

¿Qué clases contiene?
- AuthRepositoryImpl: Implementación del repositorio usando SQLAlchemy
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.domain.repositories.auth_repository import AuthRepository
from app.infrastructure.database.database import get_session
from app.infrastructure.database.models import (
    Role as RoleModel,
    AnonymousSession as AnonymousSessionModel
)

logger = logging.getLogger(__name__)


class AuthRepositoryImpl(AuthRepository):
    """
    Implementación del repositorio de autenticación usando SQLAlchemy.
    
    ¿Qué hace la clase?
    Proporciona métodos para crear y gestionar sesiones anónimas usando SQLAlchemy ORM,
    incluyendo reutilización de sesiones inactivas y actualización de actividad.
    """
    
    def __init__(self, db_service=None):
        """
        Inicializa el repositorio.
        
        ¿Qué hace la función?
        Inicializa el repositorio. El parámetro db_service se mantiene para compatibilidad
        pero no se usa, ya que SQLAlchemy maneja sus propias conexiones.
        
        ¿Qué parámetros recibe y de qué tipo?
        - db_service: Se mantiene para compatibilidad pero no se usa
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
        # db_service se mantiene para compatibilidad pero no se usa
        pass
    
    async def create_or_get_anonymous_session(self, rol: str = "gestor") -> Dict[str, Any]:
        """
        Crea una nueva sesión anónima o reutiliza una existente inactiva.
        
        ¿Qué hace la función?
        Busca primero una sesión inactiva del rol especificado para reutilizarla usando SQLAlchemy ORM.
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
            with get_session() as session:
                # Obtener o validar el ID del rol
                role = session.query(RoleModel).filter(RoleModel.nombre == rol).first()
                
                if not role:
                    # El rol no existe, usar "gestor" por defecto
                    logger.warning(f"Role '{rol}' not found, using default 'gestor'")
                    role = session.query(RoleModel).filter(RoleModel.nombre == "gestor").first()
                    
                    if not role:
                        raise Exception("Default role 'gestor' not found in database")
                
                rol_id = role.id
                rol_nombre = role.nombre
                
                # Intentar obtener una sesión inactiva primero
                inactive_session = session.query(AnonymousSessionModel).filter(
                    and_(
                        AnonymousSessionModel.is_active == False,
                        AnonymousSessionModel.rol_id == rol_id
                    )
                ).order_by(AnonymousSessionModel.created_at.asc()).first()
                
                if inactive_session:
                    # Reutilizar sesión inactiva existente
                    inactive_session.is_active = True
                    inactive_session.last_activity = datetime.utcnow()
                    
                    session.commit()
                    session.refresh(inactive_session)
                    
                    logger.info(f"Reused anonymous session ID: {inactive_session.id} with role: {rol_nombre}")
                    
                    return {
                        "id": inactive_session.id,
                        "session_id": str(inactive_session.session_id) if inactive_session.session_id else None,
                        "rol": rol_nombre,
                        "created_at": inactive_session.created_at.isoformat() if inactive_session.created_at else None
                    }
                else:
                    # Crear nueva sesión con el rol especificado
                    new_session = AnonymousSessionModel(
                        rol_id=rol_id,
                        created_at=datetime.utcnow(),
                        last_activity=datetime.utcnow(),
                        is_active=True
                    )
                    
                    session.add(new_session)
                    session.commit()
                    session.refresh(new_session)
                    
                    logger.info(f"Created new anonymous session ID: {new_session.id} with role: {rol_nombre}")
                    
                    return {
                        "id": new_session.id,
                        "session_id": str(new_session.session_id) if new_session.session_id else None,
                        "rol": rol_nombre,
                        "created_at": new_session.created_at.isoformat() if new_session.created_at else None
                    }
        except Exception as e:
            logger.error(f"Error creating/getting anonymous session: {str(e)}")
            raise Exception(f"Failed to create/get anonymous session: {str(e)}")
    
    async def update_session_activity(self, session_id: int) -> bool:
        """
        Actualiza el timestamp de última actividad de una sesión.
        
        ¿Qué hace la función?
        Actualiza el campo `last_activity` de una sesión anónima con la fecha
        y hora actual usando SQLAlchemy ORM, indicando que la sesión sigue activa.
        
        ¿Qué parámetros recibe y de qué tipo?
        - session_id (int): ID de la sesión a actualizar
        
        ¿Qué dato regresa y de qué tipo?
        - bool: True si la actualización fue exitosa, False en caso contrario
        """
        try:
            with get_session() as session:
                db_session = session.query(AnonymousSessionModel).filter(
                    AnonymousSessionModel.id == session_id
                ).first()
                
                if not db_session:
                    logger.warning(f"Session with id {session_id} not found")
                    return False
                
                db_session.last_activity = datetime.utcnow()
                session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating session activity: {str(e)}")
            return False
