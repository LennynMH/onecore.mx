# 🚀 OneCore.mx - Sistema de Análisis de Documentos con IA

Sistema completo de análisis de documentos con inteligencia artificial, desarrollado con FastAPI y React. Permite la carga, clasificación automática y extracción de datos de documentos (PDF, JPG, PNG) utilizando servicios de IA como AWS Textract y OpenAI.

---

## 📋 Tabla de Contenidos

- [Descripción](#-descripción)
- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Tecnologías](#-tecnologías)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso](#-uso)
- [APIs Disponibles](#-apis-disponibles)
- [Base de Datos](#-base-de-datos)
- [Docker](#-docker)
- [Desarrollo](#-desarrollo)
- [Producción](#-producción)
- [Estado del Proyecto](#-estado-del-proyecto)
- [Próximos Pasos](#-próximos-pasos)
- [Contribución](#-contribución)
- [Licencia](#-licencia)

---

## 🎯 Descripción

OneCore.mx es una aplicación web full-stack diseñada para el análisis inteligente de documentos. El sistema permite:

- **Carga de documentos** en formatos PDF, JPG y PNG
- **Clasificación automática** entre FACTURA e INFORMACIÓN
- **Extracción automática de datos** según el tipo de documento
- **Almacenamiento seguro** en AWS S3 y SQL Server
- **Autenticación JWT** con roles (admin, gestor)
- **Historial completo** de documentos procesados

El proyecto fue desarrollado como evaluación técnica para OneCore Virtual Core S.A. de C.V., siguiendo principios de Clean Architecture y buenas prácticas de desarrollo.

---

## ✨ Características

### Backend (FastAPI)
- ✅ **Autenticación JWT** con renovación de tokens
- ✅ **Carga de archivos CSV** con validación completa
- ✅ **Carga de documentos** (PDF, JPG, PNG) con almacenamiento en S3 y BD
- ✅ **APIs de documentos** con filtros, paginación y búsqueda
- ✅ **Integración con AWS S3** para almacenamiento
- ✅ **Integración con SQL Server** para persistencia
- ✅ **Sistema de validación mejorado** con tracking de errores en BD
- ✅ **Nombres únicos de archivos** con timestamp para evitar duplicados
- ✅ **Registro de eventos** para módulo histórico
- ✅ **Arquitectura limpia** (Clean Architecture)
- ✅ **Middleware de autenticación** y manejo de errores
- ✅ **Logging estructurado**
- ✅ **Documentación automática** con Swagger/OpenAPI
- ✅ **Soporte para múltiples ambientes** (development/production)

### Frontend (React + TypeScript)
- ✅ **Interfaz moderna** con React 18 y TypeScript
- ✅ **Autenticación JWT** con protección de rutas
- ✅ **Carga de documentos** con drag & drop
- ✅ **Visualización de resultados** de análisis
- ✅ **Historial de documentos** con filtros
- ✅ **Diseño responsive** (móvil y desktop)
- ✅ **Notificaciones** con React Toastify

### Infraestructura
- ✅ **Docker Compose** para desarrollo y producción
- ✅ **SQL Server** en contenedor Docker
- ✅ **Adminer** para gestión de base de datos
- ✅ **Inicialización automática** de base de datos

---

## 🏗️ Arquitectura

El proyecto sigue una **Arquitectura Limpia (Clean Architecture)** con separación clara de responsabilidades:

```
┌─────────────────────────────────────────────────────────┐
│                    INTERFACES (API)                      │
│  Routers, Controllers, Schemas, Dependencies            │
└──────────────────────┬──────────────────────────────────┘
                      │
┌──────────────────────▼──────────────────────────────────┐
│              APPLICATION (Use Cases)                     │
│  Lógica de negocio, Casos de uso                         │
└──────────────────────┬──────────────────────────────────┘
                      │
┌──────────────────────▼──────────────────────────────────┐
│                  DOMAIN (Entities)                        │
│  Entidades, Interfaces de repositorios                    │
└──────────────────────┬──────────────────────────────────┘
                      │
┌──────────────────────▼──────────────────────────────────┐
│            INFRASTRUCTURE (Implementations)               │
│  Repositorios, S3, SQL Server, Servicios de IA           │
└─────────────────────────────────────────────────────────┘
```

### Capas del Proyecto

1. **Core**: Configuración, seguridad, middleware, logging
2. **Domain**: Entidades y interfaces de repositorios
3. **Application**: Casos de uso (lógica de negocio)
4. **Infrastructure**: Implementaciones (S3, SQL Server, repositorios)
5. **Interfaces**: API REST, schemas, dependencias

---

## 🛠️ Tecnologías

### Backend
- **FastAPI** 0.104.1 - Framework web moderno y rápido
- **Python** 3.11+ - Lenguaje de programación
- **PyJWT** 2.8.0 - Autenticación JWT
- **boto3** 1.29.7 - SDK de AWS (S3, Textract)
- **pyodbc** 5.0.1 - Conexión a SQL Server
- **pydantic** 2.5.0 - Validación de datos
- **uvicorn** 0.24.0 - Servidor ASGI

### Frontend
- **React** 18.2.0 - Biblioteca UI
- **TypeScript** 5.3.3 - Tipado estático
- **Vite** 5.0.8 - Build tool y dev server
- **React Router** 6.20.0 - Navegación
- **Axios** 1.6.2 - Cliente HTTP
- **React Dropzone** 14.2.3 - Carga de archivos
- **React Toastify** 9.1.3 - Notificaciones
- **date-fns** 2.30.0 - Manejo de fechas

### Base de Datos
- **SQL Server** 2022 - Base de datos principal
- **PostgreSQL** (opcional) - Base de datos alternativa

### Infraestructura
- **Docker** & **Docker Compose** - Contenedores
- **AWS S3** - Almacenamiento de archivos
- **AWS Textract** (planificado) - Extracción de datos con IA
- **OpenAI** (planificado) - Análisis de sentimiento

### Herramientas de Desarrollo
- **Adminer** - Interfaz web para gestión de BD
- **Swagger/OpenAPI** - Documentación interactiva de API

---

## 📁 Estructura del Proyecto

```
onecore.mx/
├── FastAPI/                          # Backend FastAPI
│   ├── app/
│   │   ├── core/                     # Configuración, seguridad, middleware
│   │   │   ├── config.py            # Configuración de la aplicación
│   │   │   ├── security.py          # JWT y seguridad
│   │   │   ├── logging.py           # Sistema de logging
│   │   │   └── middleware/          # Middleware personalizado
│   │   │       ├── auth_middleware.py
│   │   │       ├── error_handlers.py
│   │   │       └── request_logging.py
│   │   │
│   │   ├── domain/                   # Capa de dominio
│   │   │   ├── entities/            # Entidades del dominio
│   │   │   │   ├── user.py
│   │   │   │   └── file_upload.py
│   │   │   └── repositories/         # Interfaces de repositorios
│   │   │       ├── auth_repository.py
│   │   │       └── file_repository.py
│   │   │
│   │   ├── application/              # Casos de uso
│   │   │   └── use_cases/
│   │   │       ├── auth_use_cases.py
│   │   │       └── file_upload_use_cases.py
│   │   │
│   │   ├── infrastructure/           # Implementaciones
│   │   │   ├── database/            # Conexiones a BD
│   │   │   │   ├── sql_server.py
│   │   │   │   └── postgres.py
│   │   │   ├── repositories/        # Implementaciones de repositorios
│   │   │   │   ├── auth_repository.py
│   │   │   │   └── file_repository.py
│   │   │   └── s3/                  # Servicios AWS S3
│   │   │       └── s3_service.py
│   │   │
│   │   └── interfaces/              # Capa de interfaces
│   │       ├── api/                 # API REST
│   │       │   ├── routers/         # Endpoints
│   │       │   │   ├── auth_router.py
│   │       │   │   └── file_router.py
│   │       │   └── controllers/     # Controladores
│   │       │       └── health_controller.py
│   │       ├── schemas/             # Schemas Pydantic
│   │       │   ├── auth_schema.py
│   │       │   └── file_schema.py
│   │       └── dependencies/        # Dependencias FastAPI
│   │           └── auth_dependencies.py
│   │
│   ├── main.py                      # Punto de entrada
│   ├── Dockerfile                   # Imagen Docker
│   ├── requirements.txt             # Dependencias Python
│   └── README.md                   # Documentación del backend
│
├── FrontEnd/                        # Frontend React
│   ├── src/
│   │   ├── components/             # Componentes reutilizables
│   │   │   ├── Layout.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── pages/                  # Páginas de la aplicación
│   │   │   ├── Login.tsx
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── DocumentResults.tsx
│   │   │   └── DocumentHistory.tsx
│   │   ├── services/               # Servicios
│   │   │   └── api.ts              # Cliente API
│   │   ├── App.tsx                 # Componente principal
│   │   └── main.tsx                # Punto de entrada
│   ├── package.json                # Dependencias Node.js
│   ├── vite.config.ts              # Configuración Vite
│   ├── tsconfig.json               # Configuración TypeScript
│   └── README.md                   # Documentación del frontend
│
├── BaseDatos/                       # Scripts de inicialización
│   ├── sqlserver/
│   │   ├── init.sql                # Script de inicialización SQL Server
│   │   └── init-db.sh              # Script de ejecución
│   └── postgres/
│       └── init.sql                # Script de inicialización PostgreSQL
│
├── docker-compose.development.yml   # Docker Compose para desarrollo
├── docker-compose.production.yml   # Docker Compose para producción
├── .gitignore                      # Archivos ignorados por Git
├── README.md                       # Este archivo
│
├── EVALUACION_TECNICA.txt          # Requerimientos originales (Parte 1)
├── EVALUACION_TECNICA_V2.txt       # Requerimientos extendidos (Parte 2)
├── OPCIONES_FRONTEND_CargaDocumentos.md
├── RECOMENDACIONES_Modulo_Analisis_Documentos.md
└── OneCore_API.postman_collection.json  # Colección Postman para pruebas
```

---

## 📋 Requisitos Previos

### Software Necesario
- **Docker** 20.10+ y **Docker Compose** 2.0+
- **Git** para clonar el repositorio
- **Node.js** 18+ y **npm** (solo para desarrollo frontend local)
- **Python** 3.11+ (solo para desarrollo backend local)

### Servicios Externos
- **Cuenta de AWS** con:
  - S3 bucket configurado
  - Credenciales de acceso (Access Key ID y Secret Access Key)
  - (Opcional) AWS Textract habilitado para análisis de documentos

### Opcional
- **ODBC Driver 17 for SQL Server** (solo si ejecutas la API fuera de Docker)

---

## 🚀 Instalación

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd onecore.mx
```

### 2. Configurar Variables de Entorno

#### Backend (FastAPI)

Crea los archivos de configuración en `FastAPI/`:

**`.env.development`** (desarrollo):
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

**`.env.production`** (producción):
```env
# Application Configuration
APP_NAME=OneCore API
APP_VERSION=1.0.0
DEBUG=False
ENVIRONMENT=production
LOG_LEVEL=INFO

# JWT Configuration
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

# CORS Configuration
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_ALLOW_CREDENTIALS=True

# File Upload Configuration
FILE_UPLOAD_REQUIRED_ROLE=admin
```

#### Frontend (React)

Crea el archivo `.env` en `FrontEnd/`:
```env
VITE_API_URL=http://localhost:8000
```

### 3. Levantar con Docker Compose

#### Desarrollo

```bash
docker-compose -f docker-compose.development.yml up -d
```

Esto levanta:
- ✅ SQL Server en puerto **1434** (para evitar conflictos)
- ✅ API FastAPI en puerto **8000**
- ✅ Adminer en puerto **8080**
- ✅ Inicialización automática de base de datos

#### Producción

```bash
docker-compose -f docker-compose.production.yml up -d
```

### 4. Verificar Instalación

- **API**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs (solo en desarrollo)
- **Adminer**: http://localhost:8080
  - Sistema: Microsoft SQL Server
  - Servidor: `sqlserver`
  - Usuario: `sa`
  - Contraseña: `OneCore123!` (o la configurada)
  - Base de datos: `onecore_db`

### 5. Instalar Frontend (Opcional - Desarrollo Local)

```bash
cd FrontEnd
npm install
npm run dev
```

El frontend estará disponible en: http://localhost:3000

---

## ⚙️ Configuración

### Configuración de AWS S3

1. Crea un bucket en AWS S3
2. Configura las credenciales en `.env.development` o `.env.production`
3. Asegúrate de que el bucket tenga los permisos necesarios

### Configuración de SQL Server

La base de datos se inicializa automáticamente al levantar Docker Compose. El script `BaseDatos/sqlserver/init.sql` crea:
- Base de datos `onecore_db`
- Tablas necesarias
- Roles por defecto (admin, gestor)
- Datos de ejemplo

### Configuración de CORS

En desarrollo, CORS está configurado para permitir todos los orígenes (`*`). En producción, especifica los dominios permitidos en `CORS_ORIGINS`.

---

## 📖 Uso

### 1. Iniciar Sesión

**Endpoint:** `POST /api/v1/auth/login`

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"rol": "admin"}'
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id_usuario": 999,
    "rol": "admin"
  }
}
```

### 2. Cargar Archivo CSV

**Endpoint:** `POST /api/v1/files/upload`

```bash
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@data.csv" \
  -F "param1=value1" \
  -F "param2=value2"
```

**Respuesta:**
```json
{
  "success": true,
  "message": "File uploaded successfully to S3 and database",
  "filename": "data_18122025201153.csv",
  "original_filename": "data.csv",
  "s3_key": "uploads/2025/12/18/data_18122025201153.csv",
  "s3_bucket": "onecore-uploads-dev",
  "rows_processed": 100,
  "validation_errors": [
    {
      "type": "empty_value",
      "field": "email",
      "message": "Empty value in field 'email'",
      "row": 5
    }
  ],
  "param1": "value1",
  "param2": "value2"
}
```

**Características:**
- ✅ **Nombres únicos:** El archivo se guarda con timestamp (`_ddmmyyyyhhmmss`) para evitar duplicados
- ✅ **Validación completa:** Detecta valores vacíos, tipos incorrectos y duplicados
- ✅ **Tracking de errores:** Los errores se guardan en `file_validation_errors` para consulta posterior
- ✅ **Metadatos:** `has_errors` y `error_count` en `file_uploads` para identificación rápida

### 3. Renovar Token

**Endpoint:** `POST /api/v1/auth/renew`

```bash
curl -X POST http://localhost:8000/api/v1/auth/renew \
  -H "Authorization: Bearer <token>"
```

### 4. Subir Documento (PDF, JPG, PNG)

**Endpoint:** `POST /api/v1/documents/upload`

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@documento.pdf"
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Document uploaded successfully to S3 and database",
  "document_id": 1,
  "filename": "documento_18122025201153.pdf",
  "original_filename": "documento.pdf",
  "s3_key": "documents/2025/12/18/documento_18122025201153.pdf",
  "s3_bucket": "onecore-uploads-dev",
  "classification": null,
  "extracted_data": null
}
```

### 5. Listar Documentos

**Endpoint:** `GET /api/v1/documents`

```bash
# Listar todos
curl -X GET "http://localhost:8000/api/v1/documents?page=1&limit=20" \
  -H "Authorization: Bearer <token>"

# Con filtros
curl -X GET "http://localhost:8000/api/v1/documents?classification=FACTURA&date_from=2025-12-01" \
  -H "Authorization: Bearer <token>"
```

### 6. Obtener Documento por ID

**Endpoint:** `GET /api/v1/documents/{id}`

```bash
curl -X GET "http://localhost:8000/api/v1/documents/1" \
  -H "Authorization: Bearer <token>"
```

### 7. Usar Swagger UI

Accede a http://localhost:8000/docs para probar los endpoints interactivamente.

---

## 🔌 APIs Disponibles

### Autenticación

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/login` | Iniciar sesión (obtener JWT) | No |
| POST | `/api/v1/auth/renew` | Renovar token JWT | Sí |

### Archivos

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| POST | `/api/v1/files/upload` | Subir archivo CSV | Sí (rol: admin) |

### Health Check

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| GET | `/health` | Estado de la API | No |
| GET | `/` | Información de la API | No |

### Documentos

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| POST | `/api/v1/documents/upload` | Subir documento (PDF/JPG/PNG) | Sí (rol: admin) |
| GET | `/api/v1/documents` | Listar documentos con filtros | Sí (rol: admin) |
| GET | `/api/v1/documents/{id}` | Obtener documento por ID | Sí (rol: admin) |

**Características:**
- ✅ Subida a AWS S3 y Base de Datos
- ✅ Nombres únicos con timestamp
- ✅ Filtros por clasificación y rango de fechas
- ✅ Paginación
- ✅ Registro de eventos automático
- 🚧 Clasificación automática (FASE 2 - En desarrollo)
- 🚧 Extracción de datos (FASE 3 - En desarrollo)

---

## 🗄️ Base de Datos

### Estructura de Tablas

#### `roles`
Almacena los roles del sistema (admin, gestor).

#### `anonymous_sessions`
Sesiones de usuarios anónimos con sus roles asignados.

#### `file_uploads`
Metadatos de archivos CSV subidos:
- `id`, `filename`, `s3_key`, `s3_bucket`
- `uploaded_by`, `uploaded_at`, `row_count`
- `has_errors` (BIT): Indica si el archivo tiene errores de validación
- `error_count` (INT): Número total de errores de validación

#### `file_data`
Datos de archivos CSV procesados:
- `id`, `file_id`, `row_data` (JSON), `created_at`

#### `file_validation_errors`
Errores de validación detallados:
- `id`, `file_id`, `error_type`, `field_name`
- `error_message`, `row_number`, `created_at`
- Permite consultar errores específicos por archivo, tipo o fila

#### `documents` (Nuevo - FASE 1)
Metadatos de documentos subidos (PDF, JPG, PNG):
- `id`, `filename`, `original_filename`, `file_type`
- `s3_key`, `s3_bucket`, `classification` (FACTURA/INFORMACIÓN)
- `uploaded_by`, `uploaded_at`, `processed_at`, `file_size`

#### `document_extracted_data` (Nuevo - FASE 1)
Datos extraídos de documentos:
- `id`, `document_id`, `data_type` (INVOICE/INFORMATION)
- `extracted_data` (JSON), `created_at`
- Almacena datos estructurados según tipo de documento

#### `events` (Nuevo - FASE 1)
Registro de eventos para módulo histórico:
- `id`, `event_type` (DOCUMENT_UPLOAD, AI_PROCESSING, USER_INTERACTION)
- `description`, `document_id`, `user_id`, `created_at`
- Permite tracking completo de actividades del sistema

### Scripts de Inicialización

Los scripts en `BaseDatos/sqlserver/init.sql` se ejecutan automáticamente al levantar Docker Compose.

---

## 🐳 Docker

### Servicios Docker

#### Desarrollo (`docker-compose.development.yml`)

- **sqlserver**: SQL Server 2022
- **api**: FastAPI con hot-reload
- **adminer**: Interfaz web para gestión de BD
- **init-db**: Inicialización automática de BD

#### Producción (`docker-compose.production.yml`)

- **sqlserver**: SQL Server 2022
- **api**: FastAPI optimizado para producción

### Comandos Útiles

```bash
# Ver logs
docker-compose -f docker-compose.development.yml logs -f api

# Detener servicios
docker-compose -f docker-compose.development.yml down

# Reconstruir imágenes
docker-compose -f docker-compose.development.yml build --no-cache

# Ver estado
docker-compose -f docker-compose.development.yml ps
```

---

## 💻 Desarrollo

### Backend Local (sin Docker)

```bash
cd FastAPI

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
.\venv\Scripts\Activate.ps1  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export ENV_FILE=.env.development  # Linux/Mac
# o
$env:ENV_FILE=".env.development"  # Windows PowerShell

# Ejecutar
python main.py
```

### Frontend Local

```bash
cd FrontEnd

# Instalar dependencias
npm install

# Ejecutar en desarrollo
npm run dev

# Construir para producción
npm run build
```

---

## 🚀 Producción

### Despliegue con Docker

1. Configura `.env.production` con valores de producción
2. Levanta los servicios:

```bash
docker-compose -f docker-compose.production.yml up -d
```

### Consideraciones de Producción

- ✅ Cambiar `JWT_SECRET_KEY` por una clave fuerte y única
- ✅ Cambiar `SQL_SERVER_PASSWORD` por una contraseña segura
- ✅ Configurar `CORS_ORIGINS` con dominios específicos
- ✅ Deshabilitar Swagger (`DEBUG=False`)
- ✅ Configurar logging apropiado (`LOG_LEVEL=INFO`)
- ✅ Usar HTTPS en producción
- ✅ Configurar backup de base de datos
- ✅ Monitoreo y alertas

---

## 🆕 Mejoras Recientes

### Módulo de Documentos (FASE 1) - NUEVO

- ✅ **APIs de Documentos:** 3 nuevos endpoints para subir, listar y obtener documentos
- ✅ **Soporte múltiples formatos:** PDF, JPG, PNG
- ✅ **Almacenamiento dual:** S3 y Base de Datos
- ✅ **Nombres únicos:** Timestamp automático para evitar duplicados
- ✅ **Filtros avanzados:** Por clasificación y rango de fechas
- ✅ **Paginación:** Control de resultados con page y limit
- ✅ **Registro de eventos:** Tracking automático de actividades

### Sistema de Validación Mejorado

- ✅ **Tracking de errores en BD:** Los errores de validación se guardan en la tabla `file_validation_errors` para consulta posterior
- ✅ **Campos de metadatos:** `has_errors` (BIT) y `error_count` (INT) en `file_uploads` para identificación rápida de archivos con problemas
- ✅ **Números de fila correctos:** El campo `row_number` ahora refleja correctamente el número de fila de datos (excluyendo el header)

### Nombres Únicos de Archivos

- ✅ **Timestamp automático:** Los archivos se guardan con un sufijo `_ddmmyyyyhhmmss` para evitar duplicados
- ✅ **Ejemplo:** `data.csv` → `data_18122025201153.csv`
- ✅ **Preservación del nombre original:** El campo `original_filename` mantiene el nombre original del archivo

### Base de Datos Mejorada

- ✅ **Tabla `file_validation_errors`:** Almacena errores detallados con tipo, campo, mensaje y número de fila
- ✅ **Tablas de documentos:** `documents`, `document_extracted_data`, `events` para módulo de análisis
- ✅ **Índices optimizados:** Índices en `has_errors`, `error_count` y tablas de documentos para consultas rápidas
- ✅ **Relaciones:** Foreign keys con `ON DELETE CASCADE` para mantener integridad

---

## 📊 Estado del Proyecto

### ✅ Implementado

- [x] Autenticación JWT con renovación de tokens
- [x] Carga y validación de archivos CSV
- [x] Integración con AWS S3
- [x] Integración con SQL Server
- [x] Sistema de validación mejorado con tracking de errores
- [x] Nombres únicos de archivos con timestamp
- [x] Tabla de errores de validación (`file_validation_errors`)
- [x] Campos `has_errors` y `error_count` en `file_uploads`
- [x] **Módulo de Documentos (FASE 1):** APIs para subir, listar y obtener documentos
- [x] **Tablas de documentos:** `documents`, `document_extracted_data`, `events`
- [x] Arquitectura limpia y modular
- [x] Docker Compose para desarrollo y producción
- [x] Frontend React con autenticación
- [x] Middleware de autenticación y manejo de errores
- [x] Logging estructurado
- [x] Documentación Swagger/OpenAPI
- [x] Colección Postman completa con tests automatizados

### 🚧 En Desarrollo / Planificado

- [ ] Módulo de análisis de documentos con IA (FASE 2-4)
  - [x] Carga de documentos (PDF, JPG, PNG) ✅ FASE 1
  - [ ] Clasificación automática (FACTURA/INFORMACIÓN) 🚧 FASE 2
  - [ ] Extracción de datos con AWS Textract 🚧 FASE 3
  - [ ] Análisis de sentimiento con OpenAI 🚧 FASE 3
- [ ] Historial completo de documentos (FASE 4)
  - [x] Filtros básicos (tipo, fecha) ✅ FASE 1
  - [ ] Filtro por descripción 🚧 FASE 4
  - [ ] Exportación a Excel 🚧 FASE 4
- [ ] Procesamiento asíncrono de documentos
- [ ] Integración completa con servicios de IA

---

## 🎯 Próximos Pasos

### ✅ Fase 1: Infraestructura Base - COMPLETA
- [x] Crear tablas para documentos en SQL Server
- [x] Implementar servicio de upload para PDF/JPG/PNG
- [x] Validaciones básicas (tipo, tamaño)
- [x] Integración con S3 para documentos
- [x] Endpoints de listado y obtención de documentos
- [x] Filtros básicos y paginación

### 🚧 Fase 2: Clasificación - EN DESARROLLO
- [ ] Integrar AWS Textract
- [ ] Implementar clasificación básica (FACTURA/INFORMACIÓN)
- [ ] Modificar endpoint de upload para incluir clasificación

### 🚧 Fase 3: Extracción de Datos - PENDIENTE
- [ ] Parser de facturas con Textract
- [ ] Extracción de campos clave
- [ ] Guardado estructurado en BD
- [ ] Análisis de sentimiento con OpenAI

### 🚧 Fase 4: Historial y Filtros - PENDIENTE
- [x] Endpoint de listado con filtros básicos ✅
- [ ] Filtro por descripción (búsqueda de texto)
- [ ] Exportación a Excel
- [ ] Mejoras en UI del historial

---

## 🤝 Contribución

Este proyecto fue desarrollado como evaluación técnica. Para contribuir:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Estándares de Código

- Seguir la arquitectura limpia establecida
- Escribir código documentado
- Incluir tests cuando sea posible
- Mantener commits claros y descriptivos

---

## 📄 Licencia

Proyecto de evaluación técnica - OneCore Virtual Core S.A. de C.V.

---

## 📞 Contacto y Soporte

Para preguntas o soporte, contacta al equipo de desarrollo.

---

## 🙏 Agradecimientos

- FastAPI por el excelente framework
- React por la biblioteca UI
- AWS por los servicios de IA
- La comunidad de código abierto

---

**Desarrollado con ❤️ para OneCore Virtual Core S.A. de C.V.**

