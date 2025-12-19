"""API routers."""

from fastapi import APIRouter
from .auth_router import router as auth_router
from .file_router import router as file_router
from .document_router import router as document_router
from .history_router import router as history_router

def create_api_router() -> APIRouter:
    """
    Crea el router principal de la API combinando todos los routers modulares.
    
    ¿Qué hace la función?
    Crea un router principal con prefijo /api/v1 e incluye todos los routers modulares
    (auth, file, document, history) para mantener una estructura organizada
    y escalable. Cada router maneja su propio módulo de funcionalidad.
    
    Nota: El health router se incluye directamente en main.py sin prefijo /api/v1
    porque los health checks normalmente están en la raíz de la aplicación.
    
    ¿Qué parámetros recibe y de qué tipo?
    - None
    
    ¿Qué dato regresa y de qué tipo?
    - APIRouter: Router principal de FastAPI con todos los endpoints incluidos
    """
    # Crear router principal con prefijo /api/v1
    main_router = APIRouter(prefix="/api/v1")
    
    # Incluir todos los routers modulares
    main_router.include_router(auth_router)
    main_router.include_router(file_router)
    main_router.include_router(document_router)
    main_router.include_router(history_router)
    
    return main_router

