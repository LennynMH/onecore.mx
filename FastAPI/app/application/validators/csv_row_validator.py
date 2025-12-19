"""
CSV Row Validator - Clase para validación de filas CSV.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.1

¿Qué hace este módulo?
Proporciona una clase reutilizable para validar filas de archivos CSV,
incluyendo validación de valores vacíos, tipos de datos (email, número, fecha),
y detección de duplicados. Esta refactorización extrae la lógica de validación
del FileUploadUseCases para mejorar la modularidad y reutilización.

¿Qué clases contiene?
- CSVRowValidator: Clase principal para validación de filas CSV
"""

import re
from typing import List, Dict, Any, Set
from datetime import datetime


class CSVRowValidator:
    """
    Validador de filas CSV con soporte para múltiples tipos de validación.
    
    ¿Qué hace la clase?
    Proporciona métodos estáticos y de instancia para validar filas de CSV,
    incluyendo validación de valores vacíos, tipos de datos, y detección de duplicados.
    
    ¿Qué métodos tiene?
    - validate_row: Valida una fila completa (valores vacíos y tipos)
    - validate_empty_values: Valida valores vacíos en una fila
    - validate_types: Valida tipos de datos (email, número, fecha)
    - check_duplicates: Detecta filas duplicadas
    - is_valid_email: Valida formato de email
    - is_valid_number: Valida formato numérico
    - is_valid_date: Valida formato de fecha
    """
    
    # Campos del sistema que deben ser excluidos de la validación
    SYSTEM_FIELDS: Set[str] = {'param1', 'param2'}
    
    # Patrones de nombres de campos para detección automática de tipo
    EMAIL_FIELDS: Set[str] = {'email', 'e-mail', 'correo'}
    NUMERIC_FIELDS: Set[str] = {'age', 'edad', 'id', 'number', 'numero', 'count', 'cantidad'}
    DATE_FIELDS: Set[str] = {
        'date', 'fecha', 'birthdate', 'fecha_nacimiento', 
        'created_at', 'updated_at'
    }
    
    # Formatos de fecha soportados
    DATE_FORMATS: List[str] = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%Y-%m-%d %H:%M:%S',
        '%d-%m-%Y',
        '%Y/%m/%d'
    ]
    
    @staticmethod
    def _filter_system_fields(row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filtra campos del sistema de una fila para comparación.
        
        ¿Qué hace la función?
        Crea una copia de la fila excluyendo los campos del sistema (param1, param2)
        que son agregados automáticamente y no deben considerarse en validaciones.
        
        ¿Qué parámetros recibe y de qué tipo?
        - row (Dict[str, Any]): Fila original con todos los campos
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Fila filtrada sin campos del sistema
        """
        return {k: v for k, v in row.items() if k not in CSVRowValidator.SYSTEM_FIELDS}
    
    @classmethod
    def validate_row(
        cls,
        row: Dict[str, Any],
        row_number: int
    ) -> List[Dict[str, Any]]:
        """
        Valida una fila CSV completa (valores vacíos y tipos).
        
        ¿Qué hace la función?
        Ejecuta todas las validaciones en una fila: valores vacíos y tipos de datos.
        Retorna una lista de errores encontrados.
        
        ¿Qué parámetros recibe y de qué tipo?
        - row (Dict[str, Any]): Fila a validar como diccionario
        - row_number (int): Número de fila para reporte de errores
        
        ¿Qué dato regresa y de qué tipo?
        - List[Dict[str, Any]]: Lista de errores encontrados, cada error contiene:
          - type: Tipo de error ("empty_value", "incorrect_type")
          - field: Nombre del campo con error
          - message: Mensaje descriptivo del error
          - row: Número de fila donde ocurrió el error
        """
        errors = []
        
        # Validar valores vacíos
        empty_errors = cls.validate_empty_values(row, row_number)
        errors.extend(empty_errors)
        
        # Validar tipos de datos (solo si no hay errores de valores vacíos)
        if not empty_errors:
            type_errors = cls.validate_types(row, row_number)
            errors.extend(type_errors)
        
        return errors
    
    @classmethod
    def validate_empty_values(
        cls,
        row: Dict[str, Any],
        row_number: int
    ) -> List[Dict[str, Any]]:
        """
        Valida valores vacíos en una fila CSV.
        
        ¿Qué hace la función?
        Verifica que todos los campos (excepto campos del sistema) tengan valores
        no vacíos. Campos None o strings vacíos se consideran inválidos.
        
        ¿Qué parámetros recibe y de qué tipo?
        - row (Dict[str, Any]): Fila a validar como diccionario
        - row_number (int): Número de fila para reporte de errores
        
        ¿Qué dato regresa y de qué tipo?
        - List[Dict[str, Any]]: Lista de errores de valores vacíos encontrados
        """
        errors = []
        
        for key, value in row.items():
            # Excluir campos del sistema
            if key in cls.SYSTEM_FIELDS:
                continue
            
            # Verificar si el valor está vacío
            if value is None or (isinstance(value, str) and value.strip() == ""):
                errors.append({
                    "type": "empty_value",
                    "field": key,
                    "message": f"Empty value in field '{key}'",
                    "row": row_number
                })
        
        return errors
    
    @classmethod
    def validate_types(
        cls,
        row: Dict[str, Any],
        row_number: int
    ) -> List[Dict[str, Any]]:
        """
        Valida tipos de datos en una fila CSV.
        
        ¿Qué hace la función?
        Detecta automáticamente el tipo de campo por su nombre y valida el formato
        correspondiente (email, número, fecha). Solo valida campos no vacíos.
        
        ¿Qué parámetros recibe y de qué tipo?
        - row (Dict[str, Any]): Fila a validar como diccionario
        - row_number (int): Número de fila para reporte de errores
        
        ¿Qué dato regresa y de qué tipo?
        - List[Dict[str, Any]]: Lista de errores de tipos incorrectos encontrados
        """
        errors = []
        
        for key, value in row.items():
            # Excluir campos del sistema
            if key in cls.SYSTEM_FIELDS:
                continue
            
            # Saltar valores vacíos (ya validados)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                continue
            
            key_lower = key.lower()
            
            # Validar email
            if key_lower in cls.EMAIL_FIELDS:
                if not cls.is_valid_email(value):
                    errors.append({
                        "type": "incorrect_type",
                        "field": key,
                        "message": f"Invalid email format in field '{key}': '{value}'",
                        "row": row_number
                    })
            
            # Validar campos numéricos
            elif key_lower in cls.NUMERIC_FIELDS:
                if not cls.is_valid_number(value):
                    errors.append({
                        "type": "incorrect_type",
                        "field": key,
                        "message": f"Invalid number format in field '{key}': '{value}'",
                        "row": row_number
                    })
            
            # Validar campos de fecha
            elif key_lower in cls.DATE_FIELDS:
                if not cls.is_valid_date(value):
                    errors.append({
                        "type": "incorrect_type",
                        "field": key,
                        "message": f"Invalid date format in field '{key}': '{value}'",
                        "row": row_number
                    })
        
        return errors
    
    @classmethod
    def check_duplicates(
        cls,
        row: Dict[str, Any],
        row_number: int,
        seen_rows: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detecta filas duplicadas en un conjunto de filas procesadas.
        
        ¿Qué hace la función?
        Compara la fila actual con todas las filas previamente procesadas,
        excluyendo campos del sistema. Retorna error si encuentra un duplicado.
        
        ¿Qué parámetros recibe y de qué tipo?
        - row (Dict[str, Any]): Fila actual a verificar
        - row_number (int): Número de fila actual para reporte de errores
        - seen_rows (List[Dict[str, Any]]): Lista de filas previamente procesadas
        
        ¿Qué dato regresa y de qué tipo?
        - List[Dict[str, Any]]: Lista con un error si se encuentra duplicado, lista vacía si no
        """
        errors = []
        
        # Filtrar campos del sistema para comparación
        row_for_comparison = cls._filter_system_fields(row)
        
        # Comparar con filas previamente vistas
        for idx, seen_row in enumerate(seen_rows):
            seen_row_for_comparison = cls._filter_system_fields(seen_row)
            
            if row_for_comparison == seen_row_for_comparison:
                errors.append({
                    "type": "duplicate",
                    "field": None,
                    "message": f"Duplicate row detected. Row {row_number} is identical to row {idx + 1}",
                    "row": row_number
                })
                break  # Solo reportar el primer duplicado encontrado
        
        return errors
    
    @staticmethod
    def is_valid_email(value: Any) -> bool:
        """
        Valida si un valor tiene formato de email válido.
        
        ¿Qué hace la función?
        Verifica que el valor coincida con el patrón estándar de email
        (usuario@dominio.extension).
        
        ¿Qué parámetros recibe y de qué tipo?
        - value (Any): Valor a validar (se convierte a string)
        
        ¿Qué dato regresa y de qué tipo?
        - bool: True si el valor es un email válido, False en caso contrario
        """
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, str(value).strip()))
    
    @staticmethod
    def is_valid_number(value: Any) -> bool:
        """
        Valida si un valor puede convertirse a número.
        
        ¿Qué hace la función?
        Intenta convertir el valor a float para verificar si es numérico.
        Acepta enteros y decimales.
        
        ¿Qué parámetros recibe y de qué tipo?
        - value (Any): Valor a validar (se convierte a string)
        
        ¿Qué dato regresa y de qué tipo?
        - bool: True si el valor es numérico, False en caso contrario
        """
        try:
            float(str(value).strip())
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_date(value: Any) -> bool:
        """
        Valida si un valor tiene formato de fecha válido.
        
        ¿Qué hace la función?
        Intenta parsear el valor con múltiples formatos de fecha comunes.
        Retorna True si coincide con alguno de los formatos soportados.
        
        ¿Qué parámetros recibe y de qué tipo?
        - value (Any): Valor a validar (se convierte a string)
        
        ¿Qué dato regresa y de qué tipo?
        - bool: True si el valor es una fecha válida en alguno de los formatos soportados,
          False en caso contrario
        
        Formatos soportados:
        - YYYY-MM-DD
        - DD/MM/YYYY
        - MM/DD/YYYY
        - YYYY-MM-DD HH:MM:SS
        - DD-MM-YYYY
        - YYYY/MM/DD
        """
        value_str = str(value).strip()
        
        for fmt in CSVRowValidator.DATE_FORMATS:
            try:
                datetime.strptime(value_str, fmt)
                return True
            except (ValueError, TypeError):
                continue
        
        return False

