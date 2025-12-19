"""Health check controller."""

from typing import Dict, Any
from app.core.config import settings


class HealthController:
    """
    Controlador para operaciones de health check.
    
    ¿Qué hace la clase?
    Maneja la lógica de verificación del estado de la aplicación.
    
    ¿Qué métodos tiene?
    - health_check: Verifica el estado de la aplicación
    """
    
    @staticmethod
    async def health_check() -> Dict[str, Any]:
        """
        Verifica el estado de la aplicación.
        
        ¿Qué hace la función?
        Retorna información sobre el estado de la aplicación,
        incluyendo nombre del servicio, versión y ambiente.
        
        ¿Qué parámetros recibe y de qué tipo?
        - None
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con:
            - status (str): Estado de la aplicación, siempre "healthy"
            - service (str): Nombre del servicio
            - version (str): Versión de la aplicación
            - environment (str): Ambiente de ejecución
        """
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment
        }

