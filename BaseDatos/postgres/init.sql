-- =====================================================
-- Script de Inicialización de Base de Datos PostgreSQL
-- OneCore API
-- =====================================================

-- Crear extensión para JSON si no existe
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Tabla: file_uploads
-- Almacena metadatos de los archivos CSV subidos
-- =====================================================
CREATE TABLE IF NOT EXISTS file_uploads (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    s3_key VARCHAR(500),
    s3_bucket VARCHAR(255),
    uploaded_by INTEGER,
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    row_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_file_uploads_uploaded_by ON file_uploads(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_file_uploads_uploaded_at ON file_uploads(uploaded_at);
CREATE INDEX IF NOT EXISTS idx_file_uploads_filename ON file_uploads(filename);

-- =====================================================
-- Tabla: file_data
-- Almacena los datos de cada fila del CSV procesado
-- =====================================================
CREATE TABLE IF NOT EXISTS file_data (
    id SERIAL PRIMARY KEY,
    file_id INTEGER NOT NULL,
    row_data JSONB,  -- Almacena datos de la fila como JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_file_data_file_uploads 
        FOREIGN KEY (file_id) 
        REFERENCES file_uploads(id) 
        ON DELETE CASCADE
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_file_data_file_id ON file_data(file_id);
CREATE INDEX IF NOT EXISTS idx_file_data_created_at ON file_data(created_at);
-- Índice GIN para búsquedas en JSONB
CREATE INDEX IF NOT EXISTS idx_file_data_row_data_gin ON file_data USING GIN (row_data);

-- =====================================================
-- Comentarios en las tablas
-- =====================================================
COMMENT ON TABLE file_uploads IS 'Metadatos de archivos CSV subidos a través de la API';
COMMENT ON TABLE file_data IS 'Datos procesados de cada fila del CSV, almacenados como JSON';

COMMENT ON COLUMN file_uploads.id IS 'ID único del archivo';
COMMENT ON COLUMN file_uploads.filename IS 'Nombre del archivo CSV';
COMMENT ON COLUMN file_uploads.s3_key IS 'Clave/ubicación del archivo en S3';
COMMENT ON COLUMN file_uploads.s3_bucket IS 'Bucket de S3 donde se almacena el archivo';
COMMENT ON COLUMN file_uploads.uploaded_by IS 'ID del usuario que subió el archivo';
COMMENT ON COLUMN file_uploads.uploaded_at IS 'Fecha y hora de carga del archivo';
COMMENT ON COLUMN file_uploads.row_count IS 'Número de filas procesadas del CSV';

COMMENT ON COLUMN file_data.id IS 'ID único del registro';
COMMENT ON COLUMN file_data.file_id IS 'ID del archivo relacionado (FK a file_uploads)';
COMMENT ON COLUMN file_data.row_data IS 'Datos de la fila del CSV en formato JSON';
COMMENT ON COLUMN file_data.created_at IS 'Fecha y hora de creación del registro';

-- =====================================================
-- Datos de Ejemplo (Opcional)
-- =====================================================
-- Insertar datos de ejemplo si no existen
DO $$
DECLARE
    file_id_var INTEGER;
BEGIN
    -- Verificar si ya existen datos
    IF NOT EXISTS (SELECT 1 FROM file_uploads LIMIT 1) THEN
        -- Insertar archivo de ejemplo
        INSERT INTO file_uploads (filename, s3_key, s3_bucket, uploaded_by, uploaded_at, row_count)
        VALUES (
            'example_data.csv',
            'uploads/2024/01/15/example_data.csv',
            'onecore-uploads',
            999,
            CURRENT_TIMESTAMP,
            4
        )
        RETURNING id INTO file_id_var;
        
        -- Insertar datos de ejemplo
        INSERT INTO file_data (file_id, row_data)
        VALUES 
            (file_id_var, '{"name":"John Doe","email":"john.doe@example.com","age":30,"city":"New York","param1":"value1","param2":"value2"}'::jsonb),
            (file_id_var, '{"name":"Jane Smith","email":"jane.smith@example.com","age":25,"city":"Los Angeles","param1":"value1","param2":"value2"}'::jsonb),
            (file_id_var, '{"name":"Bob Johnson","email":"bob.johnson@example.com","age":35,"city":"Chicago","param1":"value1","param2":"value2"}'::jsonb),
            (file_id_var, '{"name":"Alice Williams","email":"alice.williams@example.com","age":28,"city":"Houston","param1":"value1","param2":"value2"}'::jsonb);
    END IF;
END $$;

-- =====================================================
-- Mensaje de confirmación
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE 'Base de datos inicializada correctamente';
    RAISE NOTICE 'Tablas creadas: file_uploads, file_data';
    RAISE NOTICE 'Índices creados para optimización';
END $$;

