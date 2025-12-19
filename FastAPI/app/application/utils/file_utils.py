"""
File Utilities - Utilidades compartidas para operaciones con archivos.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.1

¿Qué hace este módulo?
Proporciona funciones utilitarias reutilizables para operaciones comunes con archivos,
como generación de nombres únicos, validación de tipos, y obtención de metadatos.
Esta refactorización centraliza código duplicado de múltiples use cases.

¿Qué funciones contiene?
- generate_unique_filename: Genera nombres únicos con timestamp
- get_file_type: Obtiene el tipo de archivo desde la extensión
- validate_file_type: Valida que el tipo de archivo sea permitido
"""

import os
from datetime import datetime
from typing import List, Optional


class FileUtils:
    """
    Utilidades para operaciones con archivos.
    
    ¿Qué hace la clase?
    Proporciona métodos estáticos para operaciones comunes con archivos:
    generación de nombres únicos, detección de tipos, y validación.
    
    ¿Qué métodos tiene?
    - generate_unique_filename: Genera nombre único con timestamp
    - get_file_type: Obtiene tipo de archivo desde extensión
    - validate_file_type: Valida tipo de archivo contra lista permitida
    """
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """
        Genera un nombre de archivo único con timestamp para evitar duplicados.
        
        ¿Qué hace la función?
        Toma el nombre original del archivo y le agrega un timestamp en formato
        ddmmyyyyhhmmss antes de la extensión, creando un nombre único que evita
        colisiones en almacenamiento.
        
        ¿Qué parámetros recibe y de qué tipo?
        - original_filename (str): Nombre original del archivo con extensión
        
        ¿Qué dato regresa y de qué tipo?
        - str: Nombre de archivo único con formato: nombre_ddmmyyyyhhmmss.extension
        
        Ejemplo:
        - Entrada: "invoice.pdf"
        - Salida: "invoice_18122025201153.pdf"
        """
        # Obtener nombre y extensión
        name, ext = os.path.splitext(original_filename)
        
        # Generar timestamp: ddmmyyyyhhmmss
        timestamp = datetime.utcnow().strftime('%d%m%Y%H%M%S')
        
        # Combinar: nombre_timestamp.extension
        unique_filename = f"{name}_{timestamp}{ext}"
        
        return unique_filename
    
    @staticmethod
    def get_file_type(filename: str) -> str:
        """
        Obtiene el tipo de archivo desde la extensión del nombre.
        
        ¿Qué hace la función?
        Extrae la extensión del nombre de archivo y la normaliza a un formato
        estándar (PDF, JPG, PNG, etc.) en mayúsculas.
        
        ¿Qué parámetros recibe y de qué tipo?
        - filename (str): Nombre del archivo con extensión
        
        ¿Qué dato regresa y de qué tipo?
        - str: Tipo de archivo en mayúsculas (PDF, JPG, PNG, etc.)
        
        Ejemplos:
        - "documento.pdf" -> "PDF"
        - "imagen.jpg" -> "JPG"
        - "foto.png" -> "PNG"
        """
        ext = os.path.splitext(filename)[1].lower()
        
        # Mapeo de extensiones comunes
        type_mapping = {
            '.pdf': 'PDF',
            '.jpg': 'JPG',
            '.jpeg': 'JPG',
            '.png': 'PNG',
            '.csv': 'CSV',
            '.txt': 'TXT',
            '.doc': 'DOC',
            '.docx': 'DOCX',
            '.xls': 'XLS',
            '.xlsx': 'XLSX'
        }
        
        return type_mapping.get(ext, ext.upper().replace('.', ''))
    
    @staticmethod
    def validate_file_type(filename: str, allowed_types: List[str]) -> bool:
        """
        Valida que el tipo de archivo esté en la lista de tipos permitidos.
        
        ¿Qué hace la función?
        Obtiene el tipo de archivo desde la extensión y verifica si está
        incluido en la lista de tipos permitidos.
        
        ¿Qué parámetros recibe y de qué tipo?
        - filename (str): Nombre del archivo con extensión
        - allowed_types (List[str]): Lista de tipos permitidos (ej: ['PDF', 'JPG', 'PNG'])
        
        ¿Qué dato regresa y de qué tipo?
        - bool: True si el tipo está permitido, False en caso contrario
        
        Ejemplo:
        - validate_file_type("documento.pdf", ["PDF", "JPG", "PNG"]) -> True
        - validate_file_type("archivo.txt", ["PDF", "JPG", "PNG"]) -> False
        """
        file_type = FileUtils.get_file_type(filename)
        return file_type in allowed_types
    
    @staticmethod
    def get_s3_path(unique_filename: str, base_path: str = "documents") -> str:
        """
        Genera la ruta S3 para un archivo basado en la fecha actual.
        
        ¿Qué hace la función?
        Crea una ruta S3 organizada por año/mes/día para facilitar la gestión
        y búsqueda de archivos almacenados.
        
        ¿Qué parámetros recibe y de qué tipo?
        - unique_filename (str): Nombre único del archivo
        - base_path (str): Ruta base (default: "documents")
        
        ¿Qué dato regresa y de qué tipo?
        - str: Ruta S3 completa con formato: base_path/YYYY/MM/DD/filename
        
        Ejemplo:
        - get_s3_path("invoice_18122025201153.pdf", "documents")
        - Salida: "documents/2025/12/18/invoice_18122025201153.pdf"
        """
        date_path = datetime.utcnow().strftime('%Y/%m/%d')
        return f"{base_path}/{date_path}/{unique_filename}"

