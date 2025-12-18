# OneCore API - FastAPI Application

Aplicación web desarrollada con FastAPI siguiendo una arquitectura limpia y modular. Implementa autenticación JWT, carga de archivos CSV con validación, integración con AWS S3 y SQL Server.

## 🏗️ Arquitectura

El proyecto sigue una arquitectura limpia (Clean Architecture) con las siguientes capas:

```
FastAPI/
├── app/
│   ├── core/              # Configuración, seguridad, middleware
│   ├── domain/            # Entidades y repositorios (interfaces)
│   ├── infrastructure/    # Implementaciones (S3, SQL Server, repositorios)
│   ├── application/       # Casos de uso (lógica de negocio)
│   └── interfaces/        # API, schemas, dependencias
└── main.py               # Punto de entrada de la aplicación
```

## 📋 Requisitos

- **Docker y Docker Compose** (para SQL Server y API)
- **AWS Account** (para S3)

**Nota:** Si ejecutas la API fuera de Docker, necesitarás:
- Python 3.9+
- ODBC Driver 17 for SQL Server instalado

## 🚀 Instalación Rápida

### 1. Clonar el repositorio

```bash
git clone <repo>
cd FastAPI
```

### 2. Crear entorno virtual

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea los archivos `.env.development` y/o `.env.production` con las siguientes variables:

#### Development (.env.development)

```env
# Application Configuration
APP_NAME=OneCore API
APP_VERSION=1.0.0
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# JWT Configuration
JWT_SECRET_KEY=dev-secret-key-change-in-production-use-strong-random-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=15
JWT_REFRESH_EXPIRATION_MINUTES=30

# SQL Server Configuration
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_SERVER_DATABASE=onecore_db
SQL_SERVER_USER=sa
SQL_SERVER_PASSWORD=OneCore123!
SQL_SERVER_DRIVER=ODBC Driver 17 for SQL Server

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key-id-dev
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key-dev
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=onecore-uploads-dev

# CORS Configuration
CORS_ORIGINS=*
CORS_ALLOW_CREDENTIALS=True

# File Upload Configuration
FILE_UPLOAD_REQUIRED_ROLE=admin
```

#### Production (.env.production)

```env
# Application Configuration
APP_NAME=OneCore API
APP_VERSION=1.0.0
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=INFO

# JWT Configuration
# ⚠️ CRÍTICO: Usa una clave secreta fuerte y única
JWT_SECRET_KEY=CHANGE_THIS_TO_A_VERY_STRONG_RANDOM_SECRET_KEY_IN_PRODUCTION
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=15
JWT_REFRESH_EXPIRATION_MINUTES=30

# SQL Server Configuration
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_SERVER_DATABASE=onecore_db
SQL_SERVER_USER=sa
SQL_SERVER_PASSWORD=CHANGE_THIS_TO_STRONG_PASSWORD
SQL_SERVER_DRIVER=ODBC Driver 17 for SQL Server

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-production-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-production-aws-secret-access-key
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=onecore-uploads-prod

# CORS Configuration (restrictivo)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_ALLOW_CREDENTIALS=True

# File Upload Configuration
FILE_UPLOAD_REQUIRED_ROLE=admin
```

⚠️ **IMPORTANTE:** Edita los valores con tus credenciales reales antes de usar.

### 5. Instalar ODBC Driver para SQL Server

**Windows:**
- Descargar e instalar desde: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
- O usar: `choco install sqlserver-odbc` (si tienes Chocolatey)

**Linux:**
```bash
# Ubuntu/Debian
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list | sudo tee /etc/apt/sources.list.d/mssql-release.list
sudo apt-get update
sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17
```

**macOS:**
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew install msodbcsql17 mssql-tools
```

### 6. Configurar Docker Compose

El proyecto usa Docker Compose para SQL Server y API. Los archivos de configuración están en:
- `docker-compose.development.yml` (desarrollo - SQL Server + API)
- `docker-compose.production.yml` (producción - SQL Server + API)

## 🐳 Docker y SQL Server

### Levantar SQL Server y API con Docker Compose

#### Development

```bash
# Desde la raíz del proyecto (onecore.mx)
docker-compose -f docker-compose.development.yml up -d
```

**Nota:** 
- Los archivos `docker-compose.*.yml` están en la raíz del proyecto
- El archivo `.env.development` se carga automáticamente mediante `env_file` en el servicio `api`

Esto levanta:
- ✅ SQL Server (puerto 1433)
- ✅ API FastAPI (puerto 8000)

**⚠️ IMPORTANTE:** SQL Server tarda ~30-60 segundos en iniciar. La API espera automáticamente a que SQL Server esté listo.

**✅ Inicialización automática:**
- El servicio `init-db` ejecuta automáticamente el script `BaseDatos/sqlserver/init.sql`
- Crea la base de datos `onecore_db`, tablas y datos de ejemplo
- No necesitas ejecutar scripts manualmente
- Adminer inicia después de que la base de datos esté lista (http://localhost:8080)

**Ver logs de la API:**
```bash
docker-compose logs -f api
```

#### Production

```bash
# Desde la raíz del proyecto (onecore.mx)
docker-compose -f docker-compose.production.yml up -d
```

**Nota:** 
- Los archivos `docker-compose.*.yml` están en la raíz del proyecto
- El archivo `.env.production` se carga automáticamente mediante `env_file` en el servicio `api`

Esto levanta:
- ✅ SQL Server (puerto 1433)
- ✅ API FastAPI (puerto 8000)

**✅ Inicialización automática:**
- El servicio `init-db` ejecuta automáticamente el script `BaseDatos/sqlserver/init.sql`
- Crea la base de datos `onecore_db`, tablas y datos de ejemplo
- No necesitas ejecutar scripts manualmente

**Ver logs de la API:**
```bash
docker-compose logs -f api
```

### Verificar SQL Server

```bash
# Ver logs
docker-compose logs sqlserver

# Ver estado
docker-compose ps

# Conectar a la base de datos
docker-compose exec sqlserver /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "OneCore123!" -C \
  -Q "SELECT @@VERSION"

# O usar Adminer (http://localhost:8080)
# Sistema: Microsoft SQL Server
# Servidor: sqlserver
# Usuario: sa
# Contraseña: OneCore123!
# Base de datos: onecore_db
```

### Detener servicios

```bash
docker-compose down
```

## 🌍 Manejo de Ambientes

El proyecto soporta dos ambientes: **development** y **production**.

### Estructura de Archivos

```
onecore.mx/                     # Raíz del proyecto
├── docker-compose.development.yml  # Desarrollo (SQL Server + API)
├── docker-compose.production.yml   # Producción (SQL Server + API)
└── FastAPI/
    ├── .env.development        # Configuración real de desarrollo (no en Git)
    └── .env.production         # Configuración real de producción (no en Git)
```

### Diferencias entre Ambientes

| Aspecto | Development | Production |
|---------|-------------|------------|
| **DEBUG** | `True` | `False` |
| **ENVIRONMENT** | `development` | `production` |
| **LOG_LEVEL** | `DEBUG` | `INFO` |
| **SQL_SERVER_DATABASE** | `onecore_db` | `onecore_db` |
| **Container** | `onecore_sqlserver_dev` | `onecore_sqlserver_prod` |
| **CORS** | `*` (permisivo) | Dominios específicos |
| **Swagger** | ✅ Habilitado | ❌ Deshabilitado |

### Variables de Entorno Importantes

#### Development

```env
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_SERVER_DATABASE=onecore_db
SQL_SERVER_USER=sa
SQL_SERVER_PASSWORD=OneCore123!
SQL_SERVER_DRIVER=ODBC Driver 17 for SQL Server
JWT_SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=*
```

#### Production

```env
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=INFO
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_SERVER_DATABASE=onecore_db
SQL_SERVER_USER=sa
SQL_SERVER_PASSWORD=CHANGE_THIS_TO_STRONG_PASSWORD
SQL_SERVER_DRIVER=ODBC Driver 17 for SQL Server
JWT_SECRET_KEY=CHANGE_THIS_TO_VERY_STRONG_RANDOM_SECRET_KEY
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## 🏃 Ejecución

### Development

**Opción 1: Todo en Docker (Recomendado)**
```bash
# Levantar SQL Server y API juntos
docker-compose -f docker-compose.development.yml up -d

# Ver logs
docker-compose -f docker-compose.development.yml logs -f api

# La API estará disponible en: http://localhost:8000
```

**Opción 2: Solo SQL Server en Docker, API local**
```bash
# Levantar solo SQL Server
docker-compose -f docker-compose.development.yml up -d sqlserver

# Ejecutar API localmente
# Windows PowerShell
$env:ENV_FILE=".env.development"; python main.py

# Linux/Mac
export ENV_FILE=.env.development; python main.py
```

**Nota:** El archivo `.env.development` debe tener `SQL_SERVER_HOST=localhost` para que la API local se conecte al SQL Server en Docker.

### Production

**Opción 1: Todo en Docker (Recomendado)**
```bash
# Levantar SQL Server y API juntos
docker-compose -f docker-compose.production.yml up -d

# Ver logs
docker-compose -f docker-compose.production.yml logs -f api

# La API estará disponible en: http://localhost:8000
```

**Opción 2: Solo SQL Server en Docker, API local**
```bash
# Levantar solo SQL Server
docker-compose -f docker-compose.production.yml up -d sqlserver

# Ejecutar API localmente
# Windows PowerShell
$env:ENV_FILE=".env.production"; python main.py

# Linux/Mac
export ENV_FILE=.env.production; python main.py
```

**Nota:** El archivo `.env.production` debe tener `SQL_SERVER_HOST=localhost` para que la API local se conecte al SQL Server en Docker.

### Con Uvicorn directamente

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

La aplicación estará disponible en: `http://localhost:8000`

Documentación interactiva (Swagger): `http://localhost:8000/docs` (solo en development)

## 📚 APIs Implementadas

### 1. API de Inicio de Sesión

**Endpoint:** `POST /api/v1/auth/login`

Permite a usuarios anónimos iniciar sesión y obtener un JWT token.

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id_usuario": 999,
    "rol": "user"
  }
}
```

**Características:**
- Token JWT firmado
- Contiene `id_usuario` y `rol`
- Expiración de 15 minutos (configurable)

### 2. API de Carga y Validación de Archivos

**Endpoint:** `POST /api/v1/files/upload`

Sube un archivo CSV junto con dos parámetros adicionales.

**Requisitos:**
- Requiere autenticación JWT
- Requiere rol específico (configurable, por defecto: `admin`)
- Archivo debe ser CSV

**Parámetros:**
- `file`: Archivo CSV (multipart/form-data)
- `param1`: Primer parámetro adicional (form-data)
- `param2`: Segundo parámetro adicional (form-data)

**Headers:**
```
Authorization: Bearer <token>
```

**Funcionalidades:**
- ✅ Subida a AWS S3
- ✅ Almacenamiento en SQL Server
- ✅ Validación de archivo (valores vacíos, tipos incorrectos, duplicados)
- ✅ Control de acceso por rol

**Respuesta:**
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "filename": "data.csv",
  "s3_key": "uploads/2024/01/15/data.csv",
  "rows_processed": 100,
  "validation_errors": [],
  "param1": "value1",
  "param2": "value2"
}
```

### 3. API de Renovación de Token

**Endpoint:** `POST /api/v1/auth/renew`

Renueva un JWT token, generando uno nuevo con tiempo de expiración adicional.

**Requisitos:**
- Token original no debe haber expirado

**Headers:**
```
Authorization: Bearer <token>
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id_usuario": 999,
    "rol": "user"
  }
}
```

## 🔐 Autenticación

Todas las APIs (excepto `/auth/login` y `/health`) requieren autenticación mediante JWT.

**Uso del token:**
```
Authorization: Bearer <token>
```

## 🧪 Pruebas

### Ejemplo con cURL

1. **Login:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login
```

2. **Cargar archivo (usar el token obtenido):**
```bash
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@data.csv" \
  -F "param1=value1" \
  -F "param2=value2"
```

3. **Renovar token:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/renew \
  -H "Authorization: Bearer <token>"
```

## 🔧 Configuración Avanzada

### Cambiar rol requerido para carga de archivos

Editar `.env.development` o `.env.production`:
```env
FILE_UPLOAD_REQUIRED_ROLE=admin
```

### Cambiar tiempo de expiración del token

Editar `.env.development` o `.env.production`:
```env
JWT_EXPIRATION_MINUTES=15
JWT_REFRESH_EXPIRATION_MINUTES=30
```

### Configurar AWS S3

Editar `.env.development` o `.env.production`:
```env
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=your-bucket-name
```

### Configurar SQL Server

Editar `.env.development` o `.env.production`:
```env
SQL_SERVER_HOST=localhost
SQL_SERVER_PORT=1433
SQL_SERVER_DATABASE=onecore_db
SQL_SERVER_USER=sa
SQL_SERVER_PASSWORD=OneCore123!
SQL_SERVER_DRIVER=ODBC Driver 17 for SQL Server
```

**⚠️ IMPORTANTE:** La contraseña de SQL Server debe cumplir con requisitos de complejidad:
- Mínimo 8 caracteres
- Al menos una mayúscula
- Al menos una minúscula
- Al menos un número
- Al menos un carácter especial (!, @, #, $, %, etc.)

## 📦 Estructura de Base de Datos

El sistema crea las siguientes tablas en SQL Server (ejecutar script de inicialización):

- **`file_uploads`**: Metadatos de archivos subidos
  - `id`, `filename`, `s3_key`, `s3_bucket`, `uploaded_by`, `uploaded_at`, `row_count`

- **`file_data`**: Datos de los archivos CSV procesados
  - `id`, `file_id`, `row_data` (NVARCHAR(MAX) - JSON), `created_at`

Las tablas se crean automáticamente al levantar Docker Compose mediante el servicio `init-db` que ejecuta `BaseDatos/sqlserver/init.sql`.

## 📝 Notas de Desarrollo

- **Arquitectura modular:** Cada capa tiene responsabilidades claras
- **Inyección de dependencias:** Uso de FastAPI dependencies
- **Manejo de errores:** Middleware centralizado para excepciones
- **Logging:** Sistema de logging estructurado
- **Validación:** Validación de datos con Pydantic
- **Ambientes separados:** Development y Production con configuraciones independientes


## 🤝 Contribución

Este proyecto fue desarrollado como evaluación técnica siguiendo estándares de desarrollo limpio y buenas prácticas.

## 📄 Licencia

Proyecto de evaluación técnica - OneCore Virtual Core S.A. de C.V.
