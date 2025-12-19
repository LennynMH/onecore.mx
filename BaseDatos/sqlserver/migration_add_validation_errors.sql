-- =====================================================
-- Migración: Agregar campo de estado y tabla de errores
-- =====================================================
-- Este script agrega:
-- 1. Campo 'has_errors' en file_uploads para indicar si hay errores
-- 2. Campo 'error_count' en file_uploads para contar errores
-- 3. Tabla 'file_validation_errors' para guardar todos los errores
-- =====================================================

USE onecore_db;
GO

-- =====================================================
-- 1. Agregar campos a file_uploads
-- =====================================================

-- Agregar campo has_errors (BIT: 0 = sin errores, 1 = con errores)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('file_uploads') AND name = 'has_errors')
BEGIN
    ALTER TABLE file_uploads
    ADD has_errors BIT DEFAULT 0;
    PRINT 'Campo has_errors agregado a file_uploads';
END
ELSE
BEGIN
    PRINT 'El campo has_errors ya existe en file_uploads';
END
GO

-- Agregar campo error_count (INT: número total de errores)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('file_uploads') AND name = 'error_count')
BEGIN
    ALTER TABLE file_uploads
    ADD error_count INT DEFAULT 0;
    PRINT 'Campo error_count agregado a file_uploads';
END
ELSE
BEGIN
    PRINT 'El campo error_count ya existe en file_uploads';
END
GO

-- =====================================================
-- 2. Crear tabla de errores de validación
-- =====================================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'file_validation_errors')
BEGIN
    CREATE TABLE file_validation_errors (
        id INT IDENTITY(1,1) PRIMARY KEY,
        file_id INT NOT NULL,
        error_type NVARCHAR(50) NOT NULL,  -- empty_value, incorrect_type, duplicate, file_structure
        field_name NVARCHAR(255),           -- Campo que tiene el error (NULL si es error de fila completa)
        error_message NVARCHAR(500) NOT NULL,
        row_number INT,                     -- Número de fila con error (NULL si es error de archivo)
        created_at DATETIME2 DEFAULT GETDATE(),
        FOREIGN KEY (file_id) REFERENCES file_uploads(id) ON DELETE CASCADE
    );
    PRINT 'Tabla file_validation_errors creada exitosamente';
END
ELSE
BEGIN
    PRINT 'La tabla file_validation_errors ya existe';
END
GO

-- =====================================================
-- 3. Crear índices para optimización
-- =====================================================

-- Índice en file_id para búsquedas rápidas
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_file_validation_errors_file_id' AND object_id = OBJECT_ID('file_validation_errors'))
BEGIN
    CREATE INDEX idx_file_validation_errors_file_id ON file_validation_errors(file_id);
    PRINT 'Índice idx_file_validation_errors_file_id creado';
END

-- Índice en error_type para filtros
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_file_validation_errors_type' AND object_id = OBJECT_ID('file_validation_errors'))
BEGIN
    CREATE INDEX idx_file_validation_errors_type ON file_validation_errors(error_type);
    PRINT 'Índice idx_file_validation_errors_type creado';
END

-- Índice en has_errors para búsquedas rápidas
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_file_uploads_has_errors' AND object_id = OBJECT_ID('file_uploads'))
BEGIN
    CREATE INDEX idx_file_uploads_has_errors ON file_uploads(has_errors);
    PRINT 'Índice idx_file_uploads_has_errors creado';
END
GO

-- =====================================================
-- 4. Actualizar registros existentes (si los hay)
-- =====================================================

-- Actualizar has_errors basado en row_count = 0 (archivos sin filas válidas)
UPDATE file_uploads
SET has_errors = 1, error_count = 0
WHERE row_count = 0 AND (has_errors IS NULL OR has_errors = 0);
GO

PRINT 'Migración completada exitosamente';
GO

