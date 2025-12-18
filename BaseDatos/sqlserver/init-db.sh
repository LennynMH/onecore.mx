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

# Ejecutar script de inicialización contra el servidor sqlserver (nombre del servicio)
/opt/mssql-tools18/bin/sqlcmd -S sqlserver -U sa -P "$PASSWORD" -C -i /docker-entrypoint-initdb.d/init.sql

echo "Inicialización completada exitosamente!"

