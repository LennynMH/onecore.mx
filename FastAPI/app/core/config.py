"""Application configuration."""

import os
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
# Prioridad: Variables de entorno del sistema > .env.{ENVIRONMENT} > .env
env_file = os.getenv("ENV_FILE", ".env")
env_path = Path(__file__).parent.parent.parent / env_file

# Cargar archivo .env si existe (en Docker, las variables vienen del sistema)
if env_path.exists():
    load_dotenv(env_path, override=True)
elif (Path(__file__).parent.parent.parent / ".env").exists():
    # Intentar cargar .env genérico si existe
    load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)
else:
    # En Docker, las variables vienen del sistema, no necesitamos archivo .env
    load_dotenv(override=False)


class Settings(BaseSettings):
    """Application settings."""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    # Configuración de la aplicación
    app_name: str = Field(default="OneCore API", json_schema_extra={"env": "APP_NAME"})
    app_version: str = Field(default="1.0.0", json_schema_extra={"env": "APP_VERSION"})
    debug: bool = Field(default=True, json_schema_extra={"env": "DEBUG"})
    environment: str = Field(default="development", json_schema_extra={"env": "ENVIRONMENT"})
    log_level: str = Field(default="INFO", json_schema_extra={"env": "LOG_LEVEL"})

    # Configuración JWT
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        json_schema_extra={"env": "JWT_SECRET_KEY"}
    )
    jwt_algorithm: str = Field(default="HS256", json_schema_extra={"env": "JWT_ALGORITHM"})
    jwt_expiration_minutes: int = Field(default=15, json_schema_extra={"env": "JWT_EXPIRATION_MINUTES"})
    jwt_refresh_expiration_minutes: int = Field(
        default=30, json_schema_extra={"env": "JWT_REFRESH_EXPIRATION_MINUTES"}
    )

    # Configuración de SQL Server
    # Nota: En Docker, usar "sqlserver" como host. En local, usar "localhost"
    sql_server_host: str = Field(default="localhost", json_schema_extra={"env": "SQL_SERVER_HOST"})
    sql_server_port: int = Field(default=1433, json_schema_extra={"env": "SQL_SERVER_PORT"})
    sql_server_database: str = Field(default="onecore_db", json_schema_extra={"env": "SQL_SERVER_DATABASE"})
    sql_server_user: str = Field(default="sa", json_schema_extra={"env": "SQL_SERVER_USER"})
    sql_server_password: str = Field(default="YourStrong@Password123", json_schema_extra={"env": "SQL_SERVER_PASSWORD"})
    sql_server_driver: str = Field(default="ODBC Driver 17 for SQL Server", json_schema_extra={"env": "SQL_SERVER_DRIVER"})

    # Configuración AWS S3
    aws_access_key_id: str | None = Field(default=None, json_schema_extra={"env": "AWS_ACCESS_KEY_ID"})
    aws_secret_access_key: str | None = Field(default=None, json_schema_extra={"env": "AWS_SECRET_ACCESS_KEY"})
    aws_region: str = Field(default="us-east-1", json_schema_extra={"env": "AWS_REGION"})
    aws_s3_bucket_name: str | None = Field(default=None, json_schema_extra={"env": "AWS_S3_BUCKET_NAME"})
    
    # Configuración AWS Textract
    aws_textract_enabled: bool = Field(default=True, json_schema_extra={"env": "AWS_TEXTRACT_ENABLED"})

    # Configuración CORS
    cors_origins: str | None = Field(default="*", json_schema_extra={"env": "CORS_ORIGINS"})
    cors_allow_credentials: bool = Field(
        default=True, json_schema_extra={"env": "CORS_ALLOW_CREDENTIALS"}
    )

    # Roles requeridos para carga de archivos (puede ser uno o varios separados por coma)
    # Compatible con FILE_UPLOAD_REQUIRED_ROLE (singular) para retrocompatibilidad
    file_upload_required_roles: str = Field(
        default="admin", 
        json_schema_extra={"env": "FILE_UPLOAD_REQUIRED_ROLES"}
    )
    
    # Mantener compatibilidad hacia atrás con FILE_UPLOAD_REQUIRED_ROLE (singular)
    file_upload_required_role: str | None = Field(
        default=None,
        json_schema_extra={"env": "FILE_UPLOAD_REQUIRED_ROLE"}
    )
    
    @property
    def file_upload_required_roles_list(self) -> list:
        """
        Convert file_upload_required_roles string to list.
        
        Soporta:
        - FILE_UPLOAD_REQUIRED_ROLES (nuevo, plural) - preferido
        - FILE_UPLOAD_REQUIRED_ROLE (antiguo, singular) - retrocompatibilidad
        
        Examples:
        - "admin" -> ["admin"]
        - "admin,gestor" -> ["admin", "gestor"]
        - "admin, gestor" -> ["admin", "gestor"] (espacios removidos)
        """
        # Prioridad: FILE_UPLOAD_REQUIRED_ROLES (plural) > FILE_UPLOAD_REQUIRED_ROLE (singular)
        roles_str = self.file_upload_required_roles or self.file_upload_required_role or "admin"
        
        if not roles_str:
            return ["admin"]  # Default
        
        # Split by comma and clean whitespace
        roles = [
            role.strip().lower()
            for role in roles_str.split(",")
            if role.strip()
        ]
        
        return roles if roles else ["admin"]  # Default if empty

    @property
    def cors_origins_list(self) -> list:
        """Convert cors_origins string to list."""
        if self.cors_origins is None:
            return ["*"]
        if isinstance(self.cors_origins, str):
            if self.cors_origins.strip():
                origins = [
                    origin.strip()
                    for origin in self.cors_origins.split(",")
                    if origin.strip()
                ]
                return origins if origins else ["*"]
            return ["*"]
        return ["*"]

    @property
    def sql_server_connection_string(self) -> str:
        """Construye la cadena de conexión a SQL Server."""
        return (
            f"DRIVER={{{self.sql_server_driver}}};"
            f"SERVER={self.sql_server_host},{self.sql_server_port};"
            f"DATABASE={self.sql_server_database};"
            f"UID={self.sql_server_user};"
            f"PWD={self.sql_server_password}"
        )


# Global settings instance
settings = Settings()

