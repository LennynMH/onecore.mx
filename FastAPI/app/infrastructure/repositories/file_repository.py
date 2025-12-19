"""
File repository implementation.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.2

¿Qué hace este módulo?
Implementa el repositorio de archivos usando SQL Server.
Delega las operaciones de base de datos al servicio SQL Server.

¿Qué clases contiene?
- FileRepositoryImpl: Implementación del repositorio de archivos
"""

from typing import List, Dict, Any
from app.domain.entities.file_upload import FileUpload
from app.domain.repositories.file_repository import FileRepository
from app.infrastructure.database.sql_server import SQLServerService


class FileRepositoryImpl(FileRepository):
    """
    Implementación del repositorio de archivos.
    
    ¿Qué hace la clase?
    Proporciona métodos para guardar datos de archivos CSV y obtener
    metadatos de archivos desde la base de datos.
    """
    
    def __init__(self, db_service: SQLServerService):
        """
        Inicializa el repositorio con el servicio de base de datos.
        
        ¿Qué hace la función?
        Configura el repositorio con el servicio de base de datos SQL Server.
        
        ¿Qué parámetros recibe y de qué tipo?
        - db_service (SQLServerService): Servicio de base de datos SQL Server
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
        self.db_service = db_service
    
    async def save_file_data(
        self,
        file_data: List[Dict[str, Any]],
        metadata: FileUpload
    ) -> bool:
        """
        Guarda los datos de un archivo CSV en la base de datos.
        
        ¿Qué hace la función?
        Almacena las filas de datos de un archivo CSV junto con sus metadatos
        (nombre, fecha de carga, errores, etc.) en la base de datos.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file_data (List[Dict[str, Any]]): Lista de filas de datos del CSV
        - metadata (FileUpload): Metadatos del archivo (nombre, fecha, errores, etc.)
        
        ¿Qué dato regresa y de qué tipo?
        - bool: True si se guardó exitosamente, False en caso contrario
        
        Raises:
            Exception: Si ocurre un error al guardar los datos
        """
        return await self.db_service.save_file_data(file_data, metadata)
    
    async def get_file_metadata(self, file_id: int) -> FileUpload:
        """
        Obtiene los metadatos de un archivo por su ID.
        
        ¿Qué hace la función?
        Busca y retorna los metadatos de un archivo guardado en la base de datos,
        incluyendo nombre, fecha de carga, estado de errores, etc.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file_id (int): ID del archivo a buscar
        
        ¿Qué dato regresa y de qué tipo?
        - FileUpload: Entidad con los metadatos del archivo
        
        Raises:
            Exception: Si el archivo no existe o hay un error al consultarlo
        """
        return await self.db_service.get_file_metadata(file_id)

