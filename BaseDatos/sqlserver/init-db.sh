#!/bin/bash
# Script para inicializar SQL Server después de que esté listo
# Este script espera a que SQL Server esté disponible y luego ejecuta init.sql

set -e

# Obtener contraseña de variable de entorno o usar default
PASSWORD="${MSSQL_SA_PASSWORD:-OneCore123!}"

echo "Esperando a que SQL Server esté listo..."

# Esperar hasta que SQL Server esté disponible (máximo 60 intentos = 5 minutos)
for i in {1..60}; do
    if /opt/mssql-tools18/bin/sqlcmd -S sqlserver -U sa -P "$PASSWORD" -C -Q "SELECT 1" &> /dev/null; then
        echo "SQL Server está listo!"
        break
    fi
    if [ $i -eq 60 ]; then
        echo "Error: SQL Server no está disponible después de 5 minutos"
        exit 1
    fi
    echo "Intento $i/60: Esperando SQL Server..."
    sleep 5
done

echo "Ejecutando script de inicialización..."

# Primero verificar que la base de datos existe, si no, crearla
echo "Verificando/Creando base de datos onecore_db..."
/opt/mssql-tools18/bin/sqlcmd -S sqlserver -U sa -P "$PASSWORD" -C -Q "IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'onecore_db') CREATE DATABASE onecore_db;" || {
    echo "Error: No se pudo crear/verificar la base de datos"
    exit 1
}

# Esperar un momento para que la base de datos esté lista
sleep 2

# Ejecutar script de inicialización contra el servidor sqlserver (nombre del servicio)
# Especificar explícitamente la base de datos onecore_db
echo "Ejecutando script SQL..."
/opt/mssql-tools18/bin/sqlcmd -S sqlserver -U sa -P "$PASSWORD" -d onecore_db -C -i /docker-entrypoint-initdb.d/init.sql

if [ $? -eq 0 ]; then
    echo "Inicialización completada exitosamente!"
    
    # Verificar que la tabla log_events se creó correctamente
    echo "Verificando creación de tablas..."
    /opt/mssql-tools18/bin/sqlcmd -S sqlserver -U sa -P "$PASSWORD" -d onecore_db -C -Q "IF EXISTS (SELECT * FROM sys.tables WHERE name = 'log_events') SELECT 'Tabla log_events creada correctamente' AS Status; ELSE SELECT 'ERROR: Tabla log_events NO existe' AS Status;"
else
    echo "Error: Hubo un problema al ejecutar el script de inicialización"
    exit 1
fi

