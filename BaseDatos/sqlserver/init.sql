-- =====================================================
-- Script de InicializaciÃ³n para SQL Server
-- =====================================================
-- NOTA: SQL Server no ejecuta automÃ¡ticamente scripts en /docker-entrypoint-initdb.d/
-- Este script debe ejecutarse manualmente despuÃ©s de que el contenedor estÃ© listo
-- O usar un contenedor separado que espere a que SQL Server estÃ© listo
--
-- Para ejecutar manualmente:
-- docker-compose exec sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "YourPassword" -i /docker-entrypoint-initdb.d/init.sql
-- =====================================================

-- Crear base de datos
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'onecore_db')
BEGIN
    CREATE DATABASE onecore_db;
    PRINT 'Base de datos onecore_db creada exitosamente';
END
ELSE
BEGIN
    PRINT 'La base de datos onecore_db ya existe';
END
GO

-- Usar la base de datos
USE onecore_db;
GO

-- =====================================================
-- CreaciÃ³n de Tablas
-- =====================================================

-- Tabla de roles
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'roles')
BEGIN
    CREATE TABLE roles (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nombre NVARCHAR(50) NOT NULL UNIQUE,
        descripcion NVARCHAR(255),
        created_at DATETIME2 DEFAULT GETDATE()
    );
    PRINT 'Tabla roles creada exitosamente';
END
ELSE
BEGIN
    PRINT 'La tabla roles ya existe';
END
GO

-- Tabla para sesiones de usuarios anÃ³nimos
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'anonymous_sessions')
BEGIN
    CREATE TABLE anonymous_sessions (
        id INT IDENTITY(1,1) PRIMARY KEY,
        session_id UNIQUEIDENTIFIER DEFAULT NEWID(),
        created_at DATETIME2 DEFAULT GETDATE(),
        last_activity DATETIME2 DEFAULT GETDATE(),
        rol_id INT NOT NULL,
        is_active BIT DEFAULT 1,
        FOREIGN KEY (rol_id) REFERENCES roles(id)
    );
    PRINT 'Tabla anonymous_sessions creada exitosamente';
END
ELSE
BEGIN
    PRINT 'La tabla anonymous_sessions ya existe';
END
GO

-- Tabla para metadatos de archivos subidos
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'file_uploads')
BEGIN
    CREATE TABLE file_uploads (
        id INT IDENTITY(1,1) PRIMARY KEY,
        filename NVARCHAR(255) NOT NULL,
        s3_key NVARCHAR(500),
        s3_bucket NVARCHAR(255),
        uploaded_by INT,
        uploaded_at DATETIME2 NOT NULL,
        row_count INT,
        created_at DATETIME2 DEFAULT GETDATE()
    );
    PRINT 'Tabla file_uploads creada exitosamente';
END
ELSE
BEGIN
    PRINT 'La tabla file_uploads ya existe';
END
GO

-- Tabla para los datos de cada fila del CSV
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'file_data')
BEGIN
    CREATE TABLE file_data (
        id INT IDENTITY(1,1) PRIMARY KEY,
        file_id INT NOT NULL,
        row_data NVARCHAR(MAX), -- Almacena los datos de la fila como JSON
        created_at DATETIME2 DEFAULT GETDATE(),
        FOREIGN KEY (file_id) REFERENCES file_uploads(id) ON DELETE CASCADE
    );
    PRINT 'Tabla file_data creada exitosamente';
END
ELSE
BEGIN
    PRINT 'La tabla file_data ya existe';
END
GO

-- =====================================================
-- Ãndices para optimizaciÃ³n
-- =====================================================

-- Ãndices en file_uploads
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_file_uploads_uploaded_by' AND object_id = OBJECT_ID('file_uploads'))
BEGIN
    CREATE INDEX idx_file_uploads_uploaded_by ON file_uploads (uploaded_by);
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_file_uploads_uploaded_at' AND object_id = OBJECT_ID('file_uploads'))
BEGIN
    CREATE INDEX idx_file_uploads_uploaded_at ON file_uploads (uploaded_at);
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_file_uploads_filename' AND object_id = OBJECT_ID('file_uploads'))
BEGIN
    CREATE INDEX idx_file_uploads_filename ON file_uploads (filename);
END

-- Ãndices en file_data
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_file_data_file_id' AND object_id = OBJECT_ID('file_data'))
BEGIN
    CREATE INDEX idx_file_data_file_id ON file_data (file_id);
END

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_file_data_created_at' AND object_id = OBJECT_ID('file_data'))
BEGIN
    CREATE INDEX idx_file_data_created_at ON file_data (created_at);
END

-- =====================================================
-- Datos de Ejemplo (Opcional)
-- =====================================================

-- Insertar roles por defecto (admin y gestor)
IF NOT EXISTS (SELECT 1 FROM roles)
BEGIN
    INSERT INTO roles (nombre, descripcion)
    VALUES
        ('admin', 'Rol de administrador con permisos completos'),
        ('gestor', 'Rol de gestor con permisos de gestiÃ³n');
    
    PRINT 'Roles por defecto insertados exitosamente';
END
ELSE
BEGIN
    PRINT 'Ya existen roles en la base de datos';
END
GO

-- Crear 5 usuarios anónimos de ejemplo para pruebas
-- 1 usuario con rol 'admin' y 4 usuarios con rol 'gestor'
IF NOT EXISTS (SELECT 1 FROM anonymous_sessions)
BEGIN
    DECLARE @admin_rol_id INT;
    DECLARE @gestor_rol_id INT;
    
    SELECT @admin_rol_id = id FROM roles WHERE nombre = 'admin';
    SELECT @gestor_rol_id = id FROM roles WHERE nombre = 'gestor';
    
    IF @admin_rol_id IS NOT NULL AND @gestor_rol_id IS NOT NULL
    BEGIN
        INSERT INTO anonymous_sessions (session_id, created_at, last_activity, rol_id, is_active)
        VALUES
            -- 1 usuario con rol admin
            (NEWID(), GETDATE(), GETDATE(), @admin_rol_id, 0),
            -- 4 usuarios con rol gestor
            (NEWID(), GETDATE(), GETDATE(), @gestor_rol_id, 0),
            (NEWID(), GETDATE(), GETDATE(), @gestor_rol_id, 0),
            (NEWID(), GETDATE(), GETDATE(), @gestor_rol_id, 0),
            (NEWID(), GETDATE(), GETDATE(), @gestor_rol_id, 0);
        
        PRINT '5 usuarios anónimos de ejemplo insertados exitosamente: 1 admin, 4 gestor';
    END
    ELSE
    BEGIN
        IF @admin_rol_id IS NULL
            PRINT 'Error: No se encontró el rol admin';
        IF @gestor_rol_id IS NULL
            PRINT 'Error: No se encontró el rol gestor';
    END
END
ELSE
BEGIN
    PRINT 'Ya existen usuarios anónimos en la base de datos';
END
GO

-- Verificar si ya existen datos
IF NOT EXISTS (SELECT 1 FROM file_uploads)
BEGIN
    -- Insertar archivo de ejemplo
    DECLARE @file_id INT;
    
    INSERT INTO file_uploads (filename, s3_key, s3_bucket, uploaded_by, uploaded_at, row_count)
    VALUES (
        'example_data.csv',
        'uploads/2024/01/15/example_data.csv',
        'onecore-uploads',
        999,
        GETDATE(),
        4
    );
    
    SET @file_id = SCOPE_IDENTITY();
    
    -- Insertar datos de ejemplo
    INSERT INTO file_data (file_id, row_data)
    VALUES
        (@file_id, '{"name":"John Doe","email":"john.doe@example.com","age":30,"city":"New York","param1":"value1","param2":"value2"}'),
        (@file_id, '{"name":"Jane Smith","email":"jane.smith@example.com","age":25,"city":"Los Angeles","param1":"value1","param2":"value2"}'),
        (@file_id, '{"name":"Bob Johnson","email":"bob.johnson@example.com","age":35,"city":"Chicago","param1":"value1","param2":"value2"}'),
        (@file_id, '{"name":"Alice Williams","email":"alice.williams@example.com","age":28,"city":"Houston","param1":"value1","param2":"value2"}');
    
    PRINT 'Datos de ejemplo insertados exitosamente';
END
ELSE
BEGIN
    PRINT 'Ya existen datos en la base de datos';
END
GO

PRINT 'Script de inicializaciÃ³n completado';
GO

