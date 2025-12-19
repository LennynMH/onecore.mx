"""
File upload controller.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.1

¿Qué hace este módulo?
Maneja la lógica de carga y validación de archivos CSV en los endpoints.
Esta refactorización utiliza HTTPHelpers para mejorar la consistencia.

¿Qué clases contiene?
- FileController: Controlador para carga de archivos CSV
"""

from fastapi import UploadFile
from app.application.use_cases.file_upload_use_cases import FileUploadUseCases
from app.interfaces.schemas.file_schema import FileUploadResponse
from app.interfaces.api.helpers import HTTPHelpers


class FileController:
    """
    Controlador para operaciones de carga de archivos CSV.
    
    ¿Qué hace la clase?
    Maneja la lógica de carga y validación de archivos CSV,
    incluyendo subida a S3 y guardado en base de datos.
    
    ¿Qué métodos tiene?
    - upload_file: Sube y valida un archivo CSV
    """
    
    def __init__(self, file_upload_use_case: FileUploadUseCases):
        """
        Inicializa el controlador con el caso de uso de carga de archivos.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file_upload_use_case (FileUploadUseCases): Instancia del caso de uso de carga de archivos
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
        self.file_upload_use_case = file_upload_use_case
    
    async def upload_file(
        self,
        file: UploadFile,
        param1: str,
        param2: str,
        user_id: int
    ) -> FileUploadResponse:
        """
        Sube un archivo CSV con validación.
        
        ¿Qué hace la función?
        Valida el tipo de archivo, lo sube a AWS S3, procesa el contenido
        y lo guarda en SQL Server. Retorna errores de validación si los hay.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file (UploadFile): Archivo CSV a subir
        - param1 (str): Primer parámetro adicional
        - param2 (str): Segundo parámetro adicional
        - user_id (int): ID del usuario que sube el archivo
        
        ¿Qué dato regresa y de qué tipo?
        - FileUploadResponse: Resultado de la carga con errores de validación si los hay
        
        Raises:
            HTTPException: Si el archivo no es CSV o hay un error en el proceso
        """
        # Validar tipo de archivo usando HTTPHelpers
        HTTPHelpers.validate_file_extension(
            file=file,
            allowed_extensions=['.csv'],
            error_message="File must be a CSV file"
        )
        
        try:
            result = await self.file_upload_use_case.upload_and_validate_file(
                file=file,
                param1=param1,
                param2=param2,
                user_id=user_id
            )
            return FileUploadResponse(**result)
        except Exception as e:
            raise HTTPHelpers.handle_controller_error(
                error=e,
                default_message=f"Error uploading file: {str(e)}"
            )

