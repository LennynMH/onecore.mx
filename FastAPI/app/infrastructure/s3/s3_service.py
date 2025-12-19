"""AWS S3 service for file storage."""

import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for AWS S3 operations."""
    
    def __init__(self):
        """
        Inicializa el servicio de AWS S3.
        
        ¿Qué hace la función?
        Configura el cliente de AWS S3 usando las credenciales de settings.
        Si las credenciales no están disponibles, el servicio queda deshabilitado
        pero no lanza errores (permite funcionamiento sin S3).
        
        ¿Qué parámetros recibe y de qué tipo?
        - Ninguno
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
        if not settings.aws_access_key_id or not settings.aws_secret_access_key:
            logger.warning("AWS credentials not configured. S3 uploads will fail.")
            self.s3_client = None
            self.bucket_name = None
        else:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            self.bucket_name = settings.aws_s3_bucket_name
    
    async def upload_file(
        self,
        file: UploadFile,
        s3_key: str
    ) -> Optional[str]:
        """
        Sube un archivo a AWS S3.
        
        ¿Qué hace la función?
        Lee el contenido del archivo y lo sube a AWS S3 en la ruta especificada.
        Si S3 no está configurado o falla la subida, retorna None sin lanzar errores
        (permite que el sistema continúe guardando solo en base de datos).
        
        ¿Qué parámetros recibe y de qué tipo?
        - file (UploadFile): Archivo FastAPI a subir
        - s3_key (str): Clave S3 (ruta) donde se guardará el archivo
        
        ¿Qué dato regresa y de qué tipo?
        - str | None: Clave S3 si la subida fue exitosa, None si S3 no está configurado o falló
        
        Raises:
            No lanza excepciones, retorna None si falla
        """
        if not self.s3_client or not self.bucket_name:
            logger.warning("AWS S3 credentials not configured. Skipping S3 upload. File will be saved to database only.")
            return None
        
        try:
            # Read file content
            file_content = await file.read()
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type or 'text/csv'
            )
            
            logger.info(f"File uploaded to S3: {s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.warning(f"Error uploading file to S3: {str(e)}. Continuing with database save only.")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error uploading file to S3: {str(e)}. Continuing with database save only.")
            return None
    
    def get_file_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Genera una URL firmada (presigned URL) para acceso temporal al archivo.
        
        ¿Qué hace la función?
        Genera una URL temporal firmada que permite acceder a un archivo en S3
        sin necesidad de credenciales AWS, útil para compartir archivos de forma segura.
        
        ¿Qué parámetros recibe y de qué tipo?
        - s3_key (str): Clave S3 (ruta) del archivo
        - expiration (int): Tiempo de expiración de la URL en segundos (default: 3600 = 1 hora)
        
        ¿Qué dato regresa y de qué tipo?
        - str: URL firmada para acceso temporal al archivo
        
        Raises:
            Exception: Si hay un error al generar la URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise Exception(f"Failed to generate file URL: {str(e)}")

