# Pruebas Unitarias - OneCore API

Este directorio contiene las pruebas unitarias para el proyecto OneCore API, implementadas según los requisitos de **PARTE 3.3: Pruebas Unitarias** de la evaluación técnica.

## 📋 Estructura

```
tests/
├── __init__.py
├── conftest.py                      # Configuración y fixtures compartidas
├── test_auth_use_cases.py           # Pruebas para AuthUseCases (20 casos)
├── test_file_upload_use_cases.py   # Pruebas para FileUploadUseCases (14 casos)
├── test_document_upload_use_cases.py # Pruebas para DocumentUploadUseCases (14 casos)
├── test_history_use_cases.py       # Pruebas para HistoryUseCases (22 casos)
└── README.md                        # Este archivo
```

## ✅ Cumplimiento de Requisitos

**PARTE 3.3: Pruebas Unitarias**
- ✅ **Al menos 10 casos de prueba por método** - CUMPLIDO
- ✅ **Utilizando Pytest** - CUMPLIDO
- ✅ **70 pruebas implementadas y verificadas**

### Resumen de Pruebas

| Use Case | Método | Casos de Prueba | Estado |
|----------|--------|-----------------|--------|
| AuthUseCases | `login_anonymous_user` | 10 | ✅ |
| AuthUseCases | `renew_token` | 10 | ✅ |
| FileUploadUseCases | `upload_and_validate_file` | 14 | ✅ |
| DocumentUploadUseCases | `upload_document` | 14 | ✅ |
| HistoryUseCases | `get_history` | 12 | ✅ |
| HistoryUseCases | `export_to_excel` | 10 | ✅ |
| **TOTAL** | **6 métodos** | **70 casos** | **✅** |

## 🚀 Ejecutar Pruebas

### Todas las pruebas
```bash
# Desde Docker
docker exec onecore_api_dev python -m pytest tests/ -v

# Localmente (requiere entorno configurado)
cd FastAPI
pytest tests/ -v
```

### Pruebas específicas
```bash
# Por archivo
pytest tests/test_auth_use_cases.py -v

# Por categoría
pytest tests/ -v -m unit          # Solo pruebas unitarias
pytest tests/ -v -m auth          # Solo pruebas de autenticación
pytest tests/ -v -m file_upload  # Solo pruebas de carga de archivos
pytest tests/ -v -m document_upload # Solo pruebas de documentos
pytest tests/ -v -m history       # Solo pruebas de historial
```

### Con cobertura
```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

### Verbose con detalles
```bash
pytest tests/ -v --tb=short
```

## 📊 Resultados de Ejecución

```
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-7.4.3
collected 70 items

======================= 70 passed, 39 warnings in 2.74s =======================
```

- ✅ **70 pruebas pasando**
- ✅ **0 pruebas fallando**
- ✅ **Tiempo de ejecución:** ~2.74 segundos

## 📝 Detalle de Pruebas por Módulo

### 1. AuthUseCases (`test_auth_use_cases.py`)

#### `login_anonymous_user` - 10 casos
1. Login con rol proporcionado
2. Login sin rol, debe usar 'gestor' por defecto
3. Login con rol=None, debe usar 'gestor' por defecto
4. Login sin repositorio, debe usar valores fallback
5. Login debe retornar estructura de token válida
6. Token generado debe ser decodificable
7. expires_in debe ser correcto (minutos * 60)
8. Login con diferentes roles debe funcionar
9. Manejo de errores del repositorio
10. Estructura de datos de usuario debe ser correcta

#### `renew_token` - 10 casos
1. Renovar token válido debe generar nuevo token
2. Renovar token debe preservar datos del usuario
3. Estructura de respuesta debe ser correcta
4. expires_in debe ser correcto (refresh_expiration_minutes * 60)
5. Renovar token inválido debe lanzar excepción
6. Renovar token expirado debe lanzar excepción
7. Renovar token vacío debe lanzar excepción
8. Estructura de datos de usuario debe ser correcta
9. Renovar token múltiples veces debe funcionar
10. Renovar token con diferentes roles debe preservar el rol

**Total: 20 pruebas**

---

### 2. FileUploadUseCases (`test_file_upload_use_cases.py`)

#### `upload_and_validate_file` - 14 casos
1. Subir CSV válido debe retornar success=True
2. Debe generar nombre único con timestamp
3. Debe detectar valores vacíos
4. Debe validar formato de email
5. Debe detectar filas duplicadas
6. Debe incluir param1 y param2 en resultado
7. Debe subir a S3 exitosamente
8. Si S3 falla, debe continuar con BD
9. Debe guardar datos en base de datos
10. Debe contar filas procesadas correctamente
11. Debe validar campos numéricos
12. Debe manejar archivo vacío
13. Debe preservar nombre original en metadata
14. Debe manejar errores de procesamiento

**Total: 14 pruebas**

---

### 3. DocumentUploadUseCases (`test_document_upload_use_cases.py`)

#### `upload_document` - 14 casos
1. Subir PDF válido debe retornar success=True
2. Debe generar nombre único con timestamp
3. Debe aceptar archivos PDF
4. Debe aceptar archivos JPG
5. Debe aceptar archivos PNG
6. Debe rechazar tipos de archivo no permitidos
7. Debe clasificar documento con Textract
8. Debe extraer datos para facturas
9. Debe subir a S3 exitosamente
10. Debe continuar si S3 falla
11. Debe guardar en base de datos
12. Debe registrar eventos
13. Debe incluir tiempo de procesamiento
14. Debe manejar errores de Textract

**Total: 14 pruebas**

---

### 4. HistoryUseCases (`test_history_use_cases.py`)

#### `get_history` - 12 casos
1. Obtener historial sin filtros debe retornar todos los eventos
2. Filtrar por tipo de evento debe funcionar
3. Filtrar por ID de documento debe funcionar
4. Filtrar por ID de usuario debe funcionar
5. Filtrar por clasificación debe funcionar
6. Filtrar por rango de fechas debe funcionar
7. Búsqueda en descripción debe funcionar
8. Paginación debe funcionar correctamente
9. Combinar múltiples filtros debe funcionar
10. Debe manejar resultados vacíos correctamente
11. Debe manejar errores del repositorio
12. Paginación por defecto debe ser page=1, page_size=50

#### `export_to_excel` - 10 casos
1. Debe crear archivo Excel
2. Debe incluir todos los eventos
3. Debe aplicar filtros al exportar
4. Debe incluir detalles del documento por defecto
5. Debe poder excluir detalles del documento
6. Debe manejar lista vacía de eventos
7. Debe filtrar por rango de fechas
8. Debe manejar errores del repositorio
9. Debe manejar grandes volúmenes de datos
10. Debe combinar todos los filtros

**Total: 22 pruebas**

---

## 🔧 Marcadores Disponibles

Las pruebas están categorizadas con marcadores para facilitar la ejecución selectiva:

- `@pytest.mark.unit`: Pruebas unitarias
- `@pytest.mark.integration`: Pruebas de integración
- `@pytest.mark.slow`: Pruebas que tardan mucho tiempo
- `@pytest.mark.auth`: Pruebas relacionadas con autenticación
- `@pytest.mark.file_upload`: Pruebas relacionadas con carga de archivos CSV
- `@pytest.mark.document_upload`: Pruebas relacionadas con carga de documentos
- `@pytest.mark.history`: Pruebas relacionadas con historial de eventos
- `@pytest.mark.s3`: Pruebas relacionadas con S3
- `@pytest.mark.database`: Pruebas relacionadas con base de datos

## 🎯 Fixtures Disponibles

Las fixtures en `conftest.py` incluyen:

### Mocks de Servicios
- `mock_auth_repository`: Repositorio de autenticación mock
- `mock_file_repository`: Repositorio de archivos mock
- `mock_document_repository`: Repositorio de documentos mock
- `mock_s3_service`: Servicio S3 mock
- `mock_textract_service`: Servicio Textract mock
- `mock_openai_service`: Servicio OpenAI mock

### Datos de Prueba
- `mock_settings`: Configuración mock
- `sample_jwt_token`: Token JWT de prueba
- `sample_user_data`: Datos de usuario de prueba
- `sample_csv_content`: Contenido CSV de prueba
- `sample_upload_file`: Archivo CSV de upload mock
- `sample_pdf_file`: Archivo PDF de prueba
- `sample_document`: Entidad Document de prueba

## 📐 Convenciones

1. **Nombres de archivos**: `test_*.py`
2. **Nombres de clases**: `Test*`
3. **Nombres de funciones**: `test_*`
4. **Documentación**: Cada test debe tener un docstring descriptivo
5. **Arrange-Act-Assert**: Seguir el patrón AAA en las pruebas
6. **Marcadores**: Usar marcadores apropiados para categorización

## 💡 Ejemplo de Prueba

```python
@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.auth
async def test_login_with_rol_provided(self, mock_auth_repository):
    """Test 1: Login con rol proporcionado."""
    # Arrange
    mock_auth_repository.create_or_get_anonymous_session = AsyncMock(
        return_value={"id": 1, "rol": "admin", "session_id": "test-session-id"}
    )
    use_case = AuthUseCases(auth_repository=mock_auth_repository)
    
    # Act
    result = await use_case.login_anonymous_user(rol="admin")
    
    # Assert
    assert result["token_type"] == "bearer"
    assert "access_token" in result
    assert result["user"]["rol"] == "admin"
    assert result["user"]["id_usuario"] == 1
    mock_auth_repository.create_or_get_anonymous_session.assert_called_once_with(rol="admin")
```

## 📈 Cobertura Objetivo

- **Mínimo 80% de cobertura** para código crítico
- **100% de cobertura** para casos de uso principales
- **Al menos 10 casos de prueba** por método público ✅ (CUMPLIDO)

## ⚠️ Notas Importantes

- Las pruebas utilizan **mocks** para evitar dependencias externas (S3, base de datos, Textract, OpenAI)
- Las pruebas asíncronas requieren `pytest-asyncio` (configurado en `pytest.ini`)
- Ver `pytest.ini` para configuración completa de pytest
- Las advertencias sobre coroutines no esperadas son esperadas cuando se usan mocks asíncronos

## 🔍 Verificación de Cumplimiento

Para verificar que todas las pruebas están funcionando:

```bash
# Ejecutar todas las pruebas
docker exec onecore_api_dev python -m pytest tests/ -v --tb=no

# Verificar resultado esperado: "70 passed"
```

**Última verificación:** 19 de Diciembre de 2025
**Estado:** ✅ **70 pruebas pasando, 0 fallando**

---

**Refactorización con Auto (Claude/ChatGPT) - PARTE 3.3**
