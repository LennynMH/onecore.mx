# 📋 RECOMENDACIONES TÉCNICAS
## Módulo de Análisis de Documentos con IA

**Fecha:** 2024-12-19  
**Basado en:** Arquitectura FastAPI existente (Clean Architecture)

---

## 🎯 RESUMEN EJECUTIVO

### Recomendación Principal
**Implementar una solución híbrida con AWS Textract como servicio principal** y OpenAI como respaldo para casos complejos, aprovechando la infraestructura AWS ya existente (S3).

### Razones:
1. ✅ Ya tienes S3 configurado (reutilización de infraestructura)
2. ✅ AWS Textract es especializado en documentos (facturas, formularios)
3. ✅ Costo-efectivo para procesamiento masivo
4. ✅ Integración nativa con S3
5. ✅ OpenAI como respaldo para análisis de sentimiento y casos complejos

---

## 🏗️ ARQUITECTURA RECOMENDADA

### 1. ESTRUCTURA DE CAPAS (Siguiendo Clean Architecture)

```
FastAPI/
├── app/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── document.py          # Entidad Document
│   │   │   ├── invoice.py          # Entidad Invoice (si es factura)
│   │   │   └── information.py      # Entidad Information (si es info)
│   │   └── repositories/
│   │       └── document_repository.py  # Interface para repositorio
│   │
│   ├── application/
│   │   └── use_cases/
│   │       ├── document_classification_use_case.py
│   │       ├── document_extraction_use_case.py
│   │       └── document_upload_use_case.py
│   │
│   ├── infrastructure/
│   │   ├── ai/
│   │   │   ├── aws_textract_service.py    # Servicio AWS Textract
│   │   │   ├── openai_service.py         # Servicio OpenAI
│   │   │   └── ai_service_factory.py     # Factory para seleccionar servicio
│   │   ├── repositories/
│   │   │   └── document_repository.py    # Implementación SQL Server
│   │   └── parsers/
│   │       ├── invoice_parser.py         # Parser para facturas
│   │       └── information_parser.py     # Parser para información
│   │
│   └── interfaces/
│       ├── api/
│       │   └── routers/
│       │       └── document_router.py    # Endpoints REST
│       └── schemas/
│           └── document_schema.py        # Pydantic schemas
```

---

## 🔧 IMPLEMENTACIÓN DETALLADA

### 1. SERVICIO DE IA - RECOMENDACIÓN PRINCIPAL

#### Opción A: AWS Textract (RECOMENDADO) ⭐

**Ventajas:**
- ✅ Especializado en documentos (facturas, formularios)
- ✅ Extracción estructurada de datos (tablas, campos clave)
- ✅ Integración nativa con S3
- ✅ Costo: ~$1.50 por 1000 páginas
- ✅ Ya tienes S3 configurado

**Desventajas:**
- ❌ No incluye análisis de sentimiento
- ❌ Requiere configuración de AWS

**Uso:**
- Clasificación: Detectar palabras clave ("factura", "invoice", "total", "subtotal")
- Extracción: Usar `analyze_document` para facturas estructuradas

#### Opción B: OpenAI GPT-4 Vision (RESPALDO)

**Ventajas:**
- ✅ Excelente para análisis de sentimiento
- ✅ Flexibilidad para casos complejos
- ✅ Puede procesar imágenes directamente

**Desventajas:**
- ❌ Más costoso (~$0.01-0.03 por imagen)
- ❌ Menos especializado en documentos estructurados

**Uso:**
- Análisis de sentimiento (para documentos tipo "Información")
- Casos complejos donde Textract falla

#### Opción C: Azure Cognitive Services (ALTERNATIVA)

**Ventajas:**
- ✅ Buena integración con Microsoft (si usas Azure)
- ✅ Document Intelligence especializado

**Desventajas:**
- ❌ Requiere cuenta Azure
- ❌ Menos común en proyectos Python

---

### 2. FLUJO DE PROCESAMIENTO RECOMENDADO

```
┌─────────────────┐
│ Usuario sube    │
│ PDF/JPG/PNG     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 1. Validar      │
│ formato/tamaño │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. Subir a S3   │
│ (almacenamiento)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. Clasificar   │
│ (Textract/OpenAI)│
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│Factura│ │Información│
└───┬────┘ └─────┬────┘
    │            │
    ▼            ▼
┌────────────┐ ┌──────────────┐
│Extraer     │ │Extraer       │
│datos factura│ │descripción   │
│            │ │+ sentimiento │
└─────┬──────┘ └──────┬───────┘
      │                │
      └────────┬───────┘
               │
               ▼
      ┌────────────────┐
      │ Guardar en SQL  │
      │ Server          │
      └────────────────┘
```

---

### 3. CLASIFICACIÓN AUTOMÁTICA

#### Estrategia Recomendada: Híbrida

**Paso 1: Análisis rápido con Textract**
```python
# Detectar palabras clave en el documento
keywords_invoice = ["factura", "invoice", "total", "subtotal", 
                    "cliente", "proveedor", "número de factura"]
keywords_info = ["información", "documento", "reporte", "análisis"]

# Si encuentra palabras de factura → FACTURA
# Si encuentra palabras de información → INFORMACIÓN
# Si no encuentra ninguna → Usar OpenAI para clasificar
```

**Paso 2: Si Textract no es concluyente → OpenAI**
```python
# Prompt para OpenAI:
"Clasifica este documento como 'FACTURA' o 'INFORMACIÓN'. 
FACTURA: contiene datos económicos/financieros, números de factura, 
totales, productos. INFORMACIÓN: texto general, reportes, análisis."
```

**Ventajas:**
- ✅ Rápido y económico (Textract primero)
- ✅ Preciso (OpenAI como respaldo)
- ✅ Costo optimizado

---

### 4. EXTRACCIÓN DE DATOS

#### Para FACTURAS (AWS Textract)

**Campos a extraer:**
```python
{
    "tipo": "FACTURA",
    "cliente": {
        "nombre": "...",
        "direccion": "..."
    },
    "proveedor": {
        "nombre": "...",
        "direccion": "..."
    },
    "numero_factura": "...",
    "fecha": "...",
    "productos": [
        {
            "cantidad": "...",
            "nombre": "...",
            "precio_unitario": "...",
            "total": "..."
        }
    ],
    "total_factura": "..."
}
```

**Implementación con Textract:**
```python
# Usar analyze_document con FORMS y TABLES
response = textract_client.analyze_document(
    Document={'S3Object': {'Bucket': bucket, 'Key': s3_key}},
    FeatureTypes=['FORMS', 'TABLES']
)

# Extraer campos clave usando Key-Value pairs
# Extraer tablas para productos
```

#### Para INFORMACIÓN (OpenAI)

**Campos a extraer:**
```python
{
    "tipo": "INFORMACIÓN",
    "descripcion": "...",
    "resumen": "...",
    "sentimiento": "positivo|negativo|neutral"
}
```

**Implementación con OpenAI:**
```python
# Usar GPT-4 Vision para procesar imagen
response = openai_client.chat.completions.create(
    model="gpt-4-vision-preview",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "Extrae descripción, resumen y analiza sentimiento"},
            {"type": "image_url", "image_url": {"url": image_url}}
        ]
    }]
)
```

---

## 💾 ESTRUCTURA DE BASE DE DATOS

### Tablas Recomendadas

```sql
-- Tabla principal de documentos
CREATE TABLE documents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    filename NVARCHAR(255) NOT NULL,
    file_type NVARCHAR(10) NOT NULL, -- PDF, JPG, PNG
    s3_key NVARCHAR(500),
    s3_bucket NVARCHAR(255),
    classification NVARCHAR(50) NOT NULL, -- FACTURA, INFORMACIÓN
    uploaded_by INT NOT NULL,
    uploaded_at DATETIME2 DEFAULT GETDATE(),
    processed_at DATETIME2,
    ai_service_used NVARCHAR(50), -- textract, openai, azure
    FOREIGN KEY (uploaded_by) REFERENCES anonymous_sessions(id)
);

-- Tabla para facturas extraídas
CREATE TABLE invoices (
    id INT IDENTITY(1,1) PRIMARY KEY,
    document_id INT NOT NULL,
    cliente_nombre NVARCHAR(255),
    cliente_direccion NVARCHAR(500),
    proveedor_nombre NVARCHAR(255),
    proveedor_direccion NVARCHAR(500),
    numero_factura NVARCHAR(100),
    fecha DATE,
    total_factura DECIMAL(18,2),
    extracted_data NVARCHAR(MAX), -- JSON con datos completos
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Tabla para productos de facturas
CREATE TABLE invoice_products (
    id INT IDENTITY(1,1) PRIMARY KEY,
    invoice_id INT NOT NULL,
    cantidad DECIMAL(18,2),
    nombre NVARCHAR(255),
    precio_unitario DECIMAL(18,2),
    total DECIMAL(18,2),
    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
);

-- Tabla para documentos tipo información
CREATE TABLE information_documents (
    id INT IDENTITY(1,1) PRIMARY KEY,
    document_id INT NOT NULL,
    descripcion NVARCHAR(MAX),
    resumen NVARCHAR(MAX),
    sentimiento NVARCHAR(20), -- positivo, negativo, neutral
    extracted_data NVARCHAR(MAX), -- JSON con datos completos
    created_at DATETIME2 DEFAULT GETDATE(),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
```

---

## 🔐 SEGURIDAD Y VALIDACIONES

### Validaciones Recomendadas

1. **Tipo de archivo:**
   ```python
   ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
   MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
   ```

2. **Límites de tamaño:**
   - PDF: Máximo 10 MB
   - Imágenes: Máximo 5 MB

3. **Validación de contenido:**
   - Verificar que el archivo no esté corrupto
   - Validar que sea realmente un PDF/imagen válido

4. **Control de acceso:**
   - Usar el mismo sistema JWT existente
   - Requerir rol específico (ej: `admin` o `gestor`)

---

## 📊 ENDPOINTS RECOMENDADOS

### 1. POST `/api/v1/documents/upload`
```json
Request:
{
    "file": <multipart/form-data>
}

Response:
{
    "success": true,
    "document_id": 123,
    "filename": "factura.pdf",
    "classification": "FACTURA",
    "s3_key": "documents/2024/12/19/factura.pdf",
    "extracted_data": {
        "cliente": {...},
        "proveedor": {...},
        "productos": [...],
        "total": 1500.00
    },
    "processing_time_ms": 2500
}
```

### 2. GET `/api/v1/documents/{document_id}`
```json
Response:
{
    "id": 123,
    "filename": "factura.pdf",
    "classification": "FACTURA",
    "extracted_data": {...},
    "uploaded_at": "2024-12-19T10:30:00",
    "processed_at": "2024-12-19T10:30:02"
}
```

### 3. GET `/api/v1/documents`
```json
Query params:
- classification: FACTURA | INFORMACIÓN
- date_from: 2024-12-01
- date_to: 2024-12-31
- page: 1
- limit: 20

Response:
{
    "total": 150,
    "page": 1,
    "limit": 20,
    "documents": [...]
}
```

---

## 💰 CONSIDERACIONES DE COSTO

### AWS Textract
- **Precio:** ~$1.50 por 1000 páginas
- **Caso:** 100 documentos/mes de 2 páginas = $0.30/mes
- **Ventaja:** Muy económico para procesamiento masivo

### OpenAI GPT-4 Vision
- **Precio:** ~$0.01-0.03 por imagen
- **Caso:** 100 documentos/mes = $1-3/mes
- **Uso:** Solo para casos complejos o análisis de sentimiento

### Estrategia de Costo Optimizado
1. Usar Textract para el 90% de los casos (facturas)
2. Usar OpenAI solo cuando:
   - Textract no puede clasificar
   - Se necesita análisis de sentimiento
   - Documentos muy complejos

**Costo estimado:** $5-10/mes para 100-200 documentos

---

## 🚀 PLAN DE IMPLEMENTACIÓN (FASES)

### Fase 1: Infraestructura Base (Semana 1)
- [ ] Crear tablas en SQL Server
- [ ] Implementar servicio de upload (similar a CSV)
- [ ] Validaciones básicas (tipo, tamaño)
- [ ] Integración con S3

### Fase 2: Clasificación (Semana 2)
- [ ] Integrar AWS Textract
- [ ] Implementar clasificación básica (palabras clave)
- [ ] Endpoint de upload con clasificación

### Fase 3: Extracción de Facturas (Semana 3)
- [ ] Parser de facturas con Textract
- [ ] Extracción de campos clave
- [ ] Guardado estructurado en BD

### Fase 4: Extracción de Información (Semana 4)
- [ ] Integrar OpenAI
- [ ] Extracción de descripción y resumen
- [ ] Análisis de sentimiento

### Fase 5: Optimización (Semana 5)
- [ ] Manejo de errores robusto
- [ ] Caché de resultados
- [ ] Logging y monitoreo

---

## 🛠️ DEPENDENCIAS NECESARIAS

```txt
# requirements.txt (adicionales)
boto3>=1.34.0              # AWS SDK (Textract, S3)
openai>=1.3.0               # OpenAI API
Pillow>=10.0.0              # Procesamiento de imágenes
PyPDF2>=3.0.0               # Lectura de PDFs (opcional)
pdf2image>=1.16.0           # Convertir PDF a imagen (opcional)
python-multipart>=0.0.6     # Ya lo tienes para FastAPI
```

---

## ⚠️ CONSIDERACIONES IMPORTANTES

### 1. Procesamiento Asíncrono
- **Recomendación:** Usar Celery o Background Tasks de FastAPI
- **Razón:** El procesamiento con IA puede tardar 2-10 segundos
- **Implementación:** Retornar `document_id` inmediatamente, procesar en background

### 2. Manejo de Errores
- Textract puede fallar con documentos de baja calidad
- Implementar retry logic (3 intentos)
- Fallback a OpenAI si Textract falla

### 3. Límites de Rate
- AWS Textract: 50 requests/segundo (suficiente)
- OpenAI: Depende del plan (gratis: 3/min, pagado: más)
- Implementar rate limiting en el API

### 4. Privacidad y Seguridad
- Los documentos pueden contener información sensible
- Encriptar documentos en S3
- Implementar políticas de retención (eliminar después de X días)

---

## 📝 EJEMPLO DE CÓDIGO (Estructura)

### Servicio AWS Textract
```python
# app/infrastructure/ai/aws_textract_service.py
import boto3
from typing import Dict, Any

class AWSTextractService:
    def __init__(self):
        self.client = boto3.client('textract')
    
    async def classify_document(self, s3_bucket: str, s3_key: str) -> str:
        """Clasifica documento como FACTURA o INFORMACIÓN"""
        response = self.client.analyze_document(
            Document={'S3Object': {'Bucket': s3_bucket, 'Key': s3_key}},
            FeatureTypes=['FORMS']
        )
        
        # Analizar texto extraído para clasificar
        text = self._extract_text(response)
        if self._is_invoice(text):
            return "FACTURA"
        return "INFORMACIÓN"
    
    async def extract_invoice_data(self, s3_bucket: str, s3_key: str) -> Dict[str, Any]:
        """Extrae datos de factura"""
        # Implementación de extracción...
        pass
```

### Use Case
```python
# app/application/use_cases/document_upload_use_case.py
class DocumentUploadUseCase:
    def __init__(self, textract_service, openai_service, document_repository):
        self.textract = textract_service
        self.openai = openai_service
        self.repository = document_repository
    
    async def upload_and_process(self, file: UploadFile, user_id: int):
        # 1. Validar y subir a S3
        s3_key = await self.upload_to_s3(file)
        
        # 2. Clasificar
        classification = await self.classify_document(s3_key)
        
        # 3. Extraer datos según tipo
        if classification == "FACTURA":
            data = await self.textract.extract_invoice_data(s3_key)
        else:
            data = await self.openai.extract_information_data(s3_key)
        
        # 4. Guardar en BD
        document = await self.repository.save_document(
            filename=file.filename,
            s3_key=s3_key,
            classification=classification,
            extracted_data=data,
            user_id=user_id
        )
        
        return document
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### Infraestructura
- [ ] Configurar AWS Textract (crear IAM role, permisos)
- [ ] Configurar OpenAI API key (si se usa)
- [ ] Crear tablas en SQL Server
- [ ] Configurar S3 bucket para documentos

### Desarrollo
- [ ] Implementar servicio AWS Textract
- [ ] Implementar servicio OpenAI (opcional)
- [ ] Crear parsers (invoice_parser, information_parser)
- [ ] Implementar use cases
- [ ] Crear endpoints REST
- [ ] Implementar validaciones

### Testing
- [ ] Pruebas unitarias de clasificación
- [ ] Pruebas de extracción de facturas
- [ ] Pruebas de extracción de información
- [ ] Pruebas de integración end-to-end

### Documentación
- [ ] Documentar endpoints (Swagger/OpenAPI)
- [ ] Documentar estructura de datos
- [ ] Guía de uso para desarrolladores

---

## 🎯 CONCLUSIÓN

**Recomendación Final:**
1. **Usar AWS Textract como servicio principal** (especializado, económico, ya tienes S3)
2. **OpenAI como respaldo** (para análisis de sentimiento y casos complejos)
3. **Procesamiento asíncrono** (mejor UX)
4. **Arquitectura modular** (siguiendo el patrón existente)

**Ventajas de esta aproximación:**
- ✅ Aprovecha infraestructura existente (S3)
- ✅ Costo-efectivo
- ✅ Escalable
- ✅ Mantenible (sigue Clean Architecture)
- ✅ Flexible (fácil agregar más servicios de IA)

---

**¿Preguntas o necesitas más detalles sobre alguna sección?**

