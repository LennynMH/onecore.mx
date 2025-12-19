"""
HTTP Helpers - Utilidades para manejo de respuestas HTTP.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.1

¿Qué hace este módulo?
Proporciona funciones helper para manejo consistente de excepciones HTTP
y validaciones comunes en los controllers.

¿Qué funciones contiene?
- handle_controller_error: Maneja excepciones de forma consistente
- validate_file_extension: Valida extensiones de archivo
"""

from fastapi import HTTPException, status
from typing import List, Optional
from fastapi import UploadFile
import os


class HTTPHelpers:
    """
    Helpers para operaciones HTTP comunes en controllers.
    
    ¿Qué hace la clase?
    Proporciona métodos estáticos para validaciones y manejo de errores
    comunes en los controllers, mejorando la consistencia y reduciendo
    código duplicado.
    
    ¿Qué métodos tiene?
    - handle_controller_error: Maneja excepciones de forma consistente
    - validate_file_extension: Valida extensiones de archivo
    """
    
    @staticmethod
    def handle_controller_error(
        error: Exception,
        default_message: str = "An error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> HTTPException:
        """
        Maneja excepciones de forma consistente en controllers.
        
        ¿Qué hace la función?
        Convierte excepciones en HTTPException con códigos de estado apropiados,
        manejando diferentes tipos de excepciones (ValueError, HTTPException, etc.)
        de forma consistente.
        
        ¿Qué parámetros recibe y de qué tipo?
        - error (Exception): Excepción a manejar
        - default_message (str): Mensaje por defecto si no se puede extraer (default: "An error occurred")
        - status_code (int): Código de estado HTTP por defecto (default: 500)
        
        ¿Qué dato regresa y de qué tipo?
        - HTTPException: Excepción HTTP lista para lanzar
        
        Ejemplo:
        ```python
        try:
            # ... operación ...
        except ValueError as e:
            raise HTTPHelpers.handle_controller_error(e, status_code=400)
        except Exception as e:
            raise HTTPHelpers.handle_controller_error(e)
        ```
        """
        # Si ya es HTTPException, retornarla directamente
        if isinstance(error, HTTPException):
            return error
        
        # Determinar código de estado según tipo de excepción
        if isinstance(error, ValueError):
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(error, FileNotFoundError):
            status_code = status.HTTP_404_NOT_FOUND
        elif isinstance(error, PermissionError):
            status_code = status.HTTP_403_FORBIDDEN
        
        # Extraer mensaje de error
        error_message = str(error) if str(error) else default_message
        
        return HTTPException(
            status_code=status_code,
            detail=error_message
        )
    
    @staticmethod
    def validate_file_extension(
        file: UploadFile,
        allowed_extensions: List[str],
        error_message: Optional[str] = None
    ) -> None:
        """
        Valida que el archivo tenga una extensión permitida.
        
        ¿Qué hace la función?
        Verifica que el nombre del archivo tenga una extensión que esté
        en la lista de extensiones permitidas. Lanza HTTPException si no es válido.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file (UploadFile): Archivo a validar
        - allowed_extensions (List[str]): Lista de extensiones permitidas (ej: ['.csv', '.pdf'])
        - error_message (Optional[str]): Mensaje de error personalizado (opcional)
        
        ¿Qué dato regresa y de qué tipo?
        - None: No retorna valor, lanza HTTPException si la validación falla
        
        Raises:
            HTTPException: Si la extensión no está permitida
        
        Ejemplo:
        ```python
        HTTPHelpers.validate_file_extension(
            file=file,
            allowed_extensions=['.csv'],
            error_message="File must be a CSV file"
        )
        ```
        """
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Obtener extensión directamente del nombre del archivo
        file_extension = os.path.splitext(file.filename)[1].lower()
        
        # Normalizar extensiones permitidas (agregar punto si no lo tienen y convertir a minúsculas)
        normalized_allowed = [
            (ext if ext.startswith('.') else f".{ext}").lower()
            for ext in allowed_extensions
        ]
        
        if file_extension not in normalized_allowed:
            if error_message:
                detail = error_message
            else:
                allowed_str = ", ".join(normalized_allowed)
                detail = f"File must have one of these extensions: {allowed_str}"
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail
            )

