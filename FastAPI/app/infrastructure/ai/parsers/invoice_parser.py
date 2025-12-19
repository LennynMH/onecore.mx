"""
Invoice Parser - Clase para parsing de datos de facturas desde Textract.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.1

¿Qué hace este módulo?
Proporciona una clase dedicada para parsear datos estructurados de facturas
desde respuestas de AWS Textract. Extrae información de cliente, proveedor,
productos, y totales usando Key-Value pairs y tablas.

¿Qué clases contiene?
- InvoiceParser: Clase principal para parsing de facturas desde Textract
"""

import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class InvoiceParser:
    """
    Parser para extraer datos estructurados de facturas desde respuestas de Textract.
    
    ¿Qué hace la clase?
    Procesa respuestas de AWS Textract (analyze_document con FORMS y TABLES)
    para extraer datos estructurados de facturas: cliente, proveedor, productos,
    número de factura, fecha, y totales.
    
    ¿Qué métodos tiene?
    - parse_invoice_from_response: Método principal para parsear desde respuesta Textract
    - extract_key_value_pairs: Extrae pares clave-valor de FORMS
    - parse_products_from_tables: Extrae productos de tablas
    - parse_invoice_from_text: Fallback usando regex en texto plano
    - Métodos auxiliares para procesamiento de bloques y celdas
    """
    
    @staticmethod
    def extract_key_value_pairs(response: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extrae pares clave-valor de la respuesta de Textract FORMS.
        
        ¿Qué hace la función?
        Procesa los bloques KEY_VALUE_SET de Textract y extrae pares clave-valor,
        preservando el orden espacial (de arriba hacia abajo) del documento.
        
        ¿Qué parámetros recibe y de qué tipo?
        - response (Dict[str, Any]): Respuesta completa de Textract analyze_document
        
        ¿Qué dato regresa y de qué tipo?
        - List[Dict[str, str]]: Lista de diccionarios con:
          - key: Clave normalizada (lowercase)
          - value: Valor asociado
          - y_position: Posición Y para ordenamiento
          - original_key: Clave original sin normalizar
        """
        key_value_pairs_list = []
        
        if 'Blocks' not in response:
            return key_value_pairs_list
        
        # Construir mapas de relaciones y bloques
        relationships = {}
        blocks_map = {}
        
        for block in response['Blocks']:
            block_id = block.get('Id')
            if block_id:
                blocks_map[block_id] = block
                if 'Relationships' in block:
                    relationships[block_id] = block['Relationships']
        
        # Encontrar pares KEY-VALUE y preservar orden
        for block in response['Blocks']:
            if block.get('BlockType') == 'KEY_VALUE_SET':
                entity_type = block.get('EntityTypes', [])
                if 'KEY' in entity_type:
                    # Este es un bloque KEY
                    key_text = InvoiceParser._get_text_from_block(block, blocks_map, relationships)
                    # Encontrar VALUE asociado
                    value_text = InvoiceParser._get_value_from_key(block, blocks_map, relationships)
                    if key_text and value_text:
                        # Obtener posición Y para preservar orden (arriba a abajo)
                        y_position = block.get('Geometry', {}).get('BoundingBox', {}).get('Top', 0)
                        key_value_pairs_list.append({
                            'key': key_text.lower(),
                            'value': value_text,
                            'y_position': y_position,
                            'original_key': key_text
                        })
                        logger.debug(f"Found key-value pair: '{key_text}' = '{value_text}' (Y: {y_position:.4f})")
        
        # Ordenar por posición Y (arriba a abajo) para preservar orden del documento
        key_value_pairs_list.sort(key=lambda x: x['y_position'])
        
        logger.info(f"Total key-value pairs extracted: {len(key_value_pairs_list)}")
        return key_value_pairs_list
    
    @staticmethod
    def _get_text_from_block(block: Dict[str, Any], blocks_map: Dict, relationships: Dict) -> str:
        """
        Obtiene texto de un bloque siguiendo sus relaciones.
        
        ¿Qué hace la función?
        Extrae el texto completo de un bloque de Textract siguiendo las relaciones
        con otros bloques (como WORD blocks relacionados).
        
        ¿Qué parámetros recibe y de qué tipo?
        - block (Dict[str, Any]): Bloque de Textract a procesar
        - blocks_map (Dict): Mapa de todos los bloques por ID
        - relationships (Dict): Mapa de relaciones entre bloques
        
        ¿Qué dato regresa y de qué tipo?
        - str: Texto extraído del bloque
        """
        text_parts = []
        block_id = block.get('Id')
        
        if block_id in relationships:
            for rel in relationships[block_id]:
                if rel.get('Type') == 'CHILD':
                    for child_id in rel.get('Ids', []):
                        child_block = blocks_map.get(child_id)
                        if child_block and child_block.get('BlockType') == 'WORD':
                            text_parts.append(child_block.get('Text', ''))
        
        return ' '.join(text_parts).strip()
    
    @staticmethod
    def _get_value_from_key(key_block: Dict[str, Any], blocks_map: Dict, relationships: Dict) -> str:
        """
        Obtiene el valor asociado a un bloque KEY.
        
        ¿Qué hace la función?
        Encuentra el bloque VALUE que está relacionado con un bloque KEY específico
        en la respuesta de Textract.
        
        ¿Qué parámetros recibe y de qué tipo?
        - key_block (Dict[str, Any]): Bloque KEY de Textract
        - blocks_map (Dict): Mapa de todos los bloques por ID
        - relationships (Dict): Mapa de relaciones entre bloques
        
        ¿Qué dato regresa y de qué tipo?
        - str: Valor asociado a la clave, o cadena vacía si no se encuentra
        """
        key_block_id = key_block.get('Id')
        
        # Buscar en todos los bloques VALUE para encontrar el que tiene relación con este KEY
        for block in blocks_map.values():
            if block.get('BlockType') == 'KEY_VALUE_SET':
                entity_types = block.get('EntityTypes', [])
                if 'VALUE' in entity_types:
                    # Verificar si este VALUE tiene relación con el KEY
                    block_id = block.get('Id')
                    if block_id in relationships:
                        for rel in relationships[block_id]:
                            if rel.get('Type') == 'VALUE':
                                # Verificar si este VALUE está relacionado con nuestro KEY
                                related_ids = rel.get('Ids', [])
                                if key_block_id in related_ids:
                                    # Este es el VALUE asociado al KEY
                                    return InvoiceParser._get_text_from_block(block, blocks_map, relationships)
        
        return ""
    
    @staticmethod
    def extract_tables(response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extrae tablas de la respuesta de Textract.
        
        ¿Qué hace la función?
        Procesa los bloques TABLE de Textract y extrae la estructura de celdas
        con sus posiciones y texto.
        
        ¿Qué parámetros recibe y de qué tipo?
        - response (Dict[str, Any]): Respuesta completa de Textract analyze_document
        
        ¿Qué dato regresa y de qué tipo?
        - List[Dict[str, Any]]: Lista de tablas, cada una con:
          - cells: Lista de celdas con row, col, text
        """
        tables = []
        
        if 'Blocks' not in response:
            return tables
        
        # Construir mapa de bloques
        blocks_map = {}
        for block in response['Blocks']:
            block_id = block.get('Id')
            if block_id:
                blocks_map[block_id] = block
        
        # Encontrar bloques TABLE
        for block in response['Blocks']:
            if block.get('BlockType') == 'TABLE':
                table_data = InvoiceParser._parse_table_block(block, list(blocks_map.values()))
                if table_data:
                    tables.append(table_data)
        
        return tables
    
    @staticmethod
    def _parse_table_block(table_block: Dict[str, Any], all_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parsea un bloque TABLE individual en estructura de celdas.
        
        ¿Qué hace la función?
        Convierte un bloque TABLE de Textract en una estructura de celdas
        con información de fila, columna y texto.
        
        ¿Qué parámetros recibe y de qué tipo?
        - table_block (Dict[str, Any]): Bloque TABLE de Textract
        - all_blocks (List[Dict[str, Any]]): Todos los bloques de la respuesta
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con:
          - cells: Lista de celdas con row, col, text
        """
        cells = []
        blocks_map = {block.get('Id'): block for block in all_blocks if block.get('Id')}
        
        # Obtener relaciones del bloque TABLE
        relationships = table_block.get('Relationships', [])
        for rel in relationships:
            if rel.get('Type') == 'CHILD':
                for cell_id in rel.get('Ids', []):
                    cell_block = blocks_map.get(cell_id)
                    if cell_block and cell_block.get('BlockType') == 'CELL':
                        row = cell_block.get('RowIndex', 0)
                        col = cell_block.get('ColumnIndex', 0)
                        text = InvoiceParser._get_text_from_cell(cell_block, blocks_map)
                        cells.append({
                            'row': row,
                            'col': col,
                            'text': text
                        })
        
        return {'cells': cells}
    
    @staticmethod
    def _get_text_from_cell(cell: Dict[str, Any], blocks_map: Dict) -> str:
        """
        Obtiene texto de una celda de tabla.
        
        ¿Qué hace la función?
        Extrae el texto completo de una celda siguiendo sus relaciones
        con bloques WORD.
        
        ¿Qué parámetros recibe y de qué tipo?
        - cell (Dict[str, Any]): Bloque CELL de Textract
        - blocks_map (Dict): Mapa de todos los bloques por ID
        
        ¿Qué dato regresa y de qué tipo?
        - str: Texto extraído de la celda
        """
        text_parts = []
        cell_id = cell.get('Id')
        
        if 'Relationships' in cell:
            for rel in cell['Relationships']:
                if rel.get('Type') == 'CHILD':
                    for child_id in rel.get('Ids', []):
                        child_block = blocks_map.get(child_id)
                        if child_block and child_block.get('BlockType') == 'WORD':
                            text_parts.append(child_block.get('Text', ''))
        
        return ' '.join(text_parts).strip()
    
    @staticmethod
    def parse_products_from_tables(tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parsea productos desde datos de tablas.
        
        ¿Qué hace la función?
        Identifica la fila de encabezados y mapea columnas a campos de productos
        (cantidad, nombre, precio_unitario, total), luego extrae los datos
        de cada fila de producto.
        
        ¿Qué parámetros recibe y de qué tipo?
        - tables (List[Dict[str, Any]]): Lista de tablas extraídas de Textract
        
        ¿Qué dato regresa y de qué tipo?
        - List[Dict[str, Any]]: Lista de productos, cada uno con:
          - cantidad: Cantidad del producto
          - nombre: Nombre/descripción del producto
          - precio_unitario: Precio unitario
          - total: Total del producto
        """
        products = []
        
        for table in tables:
            cells = table.get('cells', [])
            if not cells:
                continue
            
            # Agrupar celdas por fila
            rows = {}
            for cell in cells:
                row = cell.get('row', 0)
                col = cell.get('col', 0)
                text = cell.get('text', '').strip()
                
                if row not in rows:
                    rows[row] = {}
                rows[row][col] = text
            
            if not rows:
                continue
            
            # Encontrar fila de encabezados (usualmente fila 1, pero podría ser 0)
            header_row_num = None
            column_mapping = {}  # Mapea índice de columna a nombre de campo
            
            # Intentar encontrar fila de encabezados
            for row_num in sorted(rows.keys()):
                row_data = rows[row_num]
                header_texts = [rows[row_num].get(col, '').lower() for col in sorted(row_data.keys())]
                header_text = ' '.join(header_texts)
                
                # Verificar si parece una fila de encabezados
                if any(keyword in header_text for keyword in ['cantidad', 'producto', 'precio', 'unitario', 'total', 'descripcion']):
                    header_row_num = row_num
                    # Mapear columnas basado en contenido del encabezado
                    for col_num in sorted(row_data.keys()):
                        header_cell = row_data[col_num].lower().strip()
                        
                        if 'cantidad' in header_cell or 'qty' in header_cell:
                            column_mapping[col_num] = 'cantidad'
                        elif 'producto' in header_cell or 'descripcion' in header_cell or 'nombre' in header_cell or 'item' in header_cell:
                            column_mapping[col_num] = 'nombre'
                        elif 'precio' in header_cell and 'unitario' in header_cell:
                            column_mapping[col_num] = 'precio_unitario'
                        elif 'precio' in header_cell and 'unitario' not in header_cell:
                            # Podría ser precio unitario o total, verificar posición
                            if not column_mapping.get('precio_unitario'):
                                column_mapping[col_num] = 'precio_unitario'
                        elif 'total' in header_cell and 'precio' not in header_cell:
                            column_mapping[col_num] = 'total'
                    
                    break
            
            # Si no se encontró encabezado, usar mapeo por defecto
            if not header_row_num:
                header_row_num = min(rows.keys()) if rows else 1
                # Mapeo por defecto: asumir orden: cantidad, nombre, precio_unitario, total
                sorted_cols = sorted(rows[header_row_num].keys()) if header_row_num in rows else []
                if len(sorted_cols) >= 4:
                    column_mapping[sorted_cols[0]] = 'cantidad'
                    column_mapping[sorted_cols[1]] = 'nombre'
                    column_mapping[sorted_cols[2]] = 'precio_unitario'
                    column_mapping[sorted_cols[3]] = 'total'
                elif len(sorted_cols) == 3:
                    column_mapping[sorted_cols[0]] = 'cantidad'
                    column_mapping[sorted_cols[1]] = 'nombre'
                    column_mapping[sorted_cols[2]] = 'total'
            
            # Parsear filas de datos
            for row_num in sorted(rows.keys()):
                if row_num == header_row_num:  # Saltar fila de encabezados
                    continue
                
                row_data = rows[row_num]
                product = {}
                
                # Extraer datos basado en mapeo de columnas
                for col_num in sorted(row_data.keys()):
                    text = row_data[col_num].strip()
                    if not text:
                        continue
                    
                    field_name = column_mapping.get(col_num)
                    if field_name:
                        if field_name in ['precio_unitario', 'total']:
                            # Extraer monto, preservando formato
                            amount = InvoiceParser._extract_amount(text)
                            if amount:
                                product[field_name] = amount
                            else:
                                # Si la extracción falla, usar texto original
                                product[field_name] = text
                        else:
                            product[field_name] = text
                    else:
                        # Fallback: intentar identificar por contenido si no hay mapeo
                        if not product.get("cantidad") and InvoiceParser._is_numeric(text) and not ('$' in text or InvoiceParser._is_amount(text)):
                            product["cantidad"] = text
                        elif not product.get("nombre") and not InvoiceParser._is_amount(text):
                            product["nombre"] = text
                        elif not product.get("precio_unitario") and ('$' in text or InvoiceParser._is_amount(text)):
                            amount = InvoiceParser._extract_amount(text)
                            if amount:
                                product["precio_unitario"] = amount
                        elif not product.get("total") and ('$' in text or InvoiceParser._is_amount(text)):
                            amount = InvoiceParser._extract_amount(text)
                            if amount:
                                product["total"] = amount
                
                # Solo agregar producto si tiene al menos nombre o cantidad
                if product.get("nombre") or product.get("cantidad"):
                    products.append(product)
        
        return products
    
    @staticmethod
    def _is_numeric(text: str) -> bool:
        """
        Verifica si un texto es numérico.
        
        ¿Qué hace la función?
        Intenta convertir el texto a número flotante, removiendo comas y símbolos de moneda.
        
        ¿Qué parámetros recibe y de qué tipo?
        - text (str): Texto a verificar
        
        ¿Qué dato regresa y de qué tipo?
        - bool: True si el texto es numérico, False en caso contrario
        """
        try:
            float(text.replace(',', '').replace('$', '').strip())
            return True
        except:
            return False
    
    @staticmethod
    def _is_amount(text: str) -> bool:
        """
        Verifica si un texto parece ser un monto.
        
        ¿Qué hace la función?
        Verifica si el texto contiene símbolo de dólar o dígitos.
        
        ¿Qué parámetros recibe y de qué tipo?
        - text (str): Texto a verificar
        
        ¿Qué dato regresa y de qué tipo?
        - bool: True si parece ser un monto, False en caso contrario
        """
        return '$' in text or any(char.isdigit() for char in text)
    
    @staticmethod
    def _extract_amount(text: str) -> Optional[str]:
        """
        Extrae monto de un texto (remueve símbolos de moneda, mantiene números).
        
        ¿Qué hace la función?
        Busca un patrón numérico en el texto y lo extrae, removiendo símbolos
        de moneda y comas.
        
        ¿Qué parámetros recibe y de qué tipo?
        - text (str): Texto del cual extraer el monto
        
        ¿Qué dato regresa y de qué tipo?
        - Optional[str]: Monto extraído como string, o None si no se encuentra
        """
        if not text:
            return None
        
        # Remover símbolos de moneda y extraer números
        # Coincidir números con decimales opcionales
        match = re.search(r'[\d,]+\.?\d*', text.replace('$', '').replace(',', ''))
        if match:
            return match.group(0)
        return None
    
    @staticmethod
    def parse_invoice_from_text(raw_text: str) -> Dict[str, Any]:
        """
        Fallback: Parsea datos de factura desde texto plano usando patrones regex.
        
        ¿Qué hace la función?
        Usa expresiones regulares para extraer información de factura desde texto plano
        cuando el análisis estructurado de Textract no está disponible o falla.
        Busca secciones como "DATOS DEL CLIENTE" y "DATOS DEL PROVEEDOR".
        
        ¿Qué parámetros recibe y de qué tipo?
        - raw_text (str): Texto plano del documento
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con datos extraídos:
          - cliente: {nombre, direccion, rfc}
          - proveedor: {nombre, direccion, rfc}
          - numero_factura: Número de factura
          - fecha: Fecha de la factura
          - total: Total de la factura
        """
        data = {
            "cliente": {},
            "proveedor": {}
        }
        
        # Extraer cliente - buscar sección "DATOS DEL CLIENTE"
        cliente_section_pattern = r'DATOS\s+DEL\s+CLIENTE[^\n]*\n(.*?)(?=DATOS\s+DEL\s+PROVEEDOR|DETALLE|$)'
        cliente_match = re.search(cliente_section_pattern, raw_text, re.IGNORECASE | re.DOTALL)
        if cliente_match:
            cliente_text = cliente_match.group(1)
            
            # Extraer nombre
            nombre_match = re.search(r'Nombre\s*:?\s*([^\n]+)', cliente_text, re.IGNORECASE)
            if nombre_match:
                data["cliente"]["nombre"] = nombre_match.group(1).strip()
            
            # Extraer dirección
            direccion_match = re.search(r'Direcci[oó]n\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=RFC|$)', cliente_text, re.IGNORECASE)
            if direccion_match:
                direccion = direccion_match.group(1).strip()
                # Limpiar múltiples líneas
                direccion = ' '.join(line.strip() for line in direccion.split('\n') if line.strip())
                data["cliente"]["direccion"] = direccion
            
            # Extraer RFC
            rfc_match = re.search(r'RFC\s*:?\s*([A-Z0-9]+)', cliente_text, re.IGNORECASE)
            if rfc_match:
                data["cliente"]["rfc"] = rfc_match.group(1).strip()
        
        # Extraer proveedor - buscar sección "DATOS DEL PROVEEDOR"
        proveedor_section_pattern = r'DATOS\s+DEL\s+PROVEEDOR[^\n]*\n(.*?)(?=DETALLE|TOTAL|$)'
        proveedor_match = re.search(proveedor_section_pattern, raw_text, re.IGNORECASE | re.DOTALL)
        if proveedor_match:
            proveedor_text = proveedor_match.group(1)
            
            # Extraer nombre
            nombre_match = re.search(r'Nombre\s*:?\s*([^\n]+)', proveedor_text, re.IGNORECASE)
            if nombre_match:
                data["proveedor"]["nombre"] = nombre_match.group(1).strip()
            
            # Extraer dirección
            direccion_match = re.search(r'Direcci[oó]n\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=RFC|$)', proveedor_text, re.IGNORECASE)
            if direccion_match:
                direccion = direccion_match.group(1).strip()
                # Limpiar múltiples líneas
                direccion = ' '.join(line.strip() for line in direccion.split('\n') if line.strip())
                data["proveedor"]["direccion"] = direccion
            
            # Extraer RFC
            rfc_match = re.search(r'RFC\s*:?\s*([A-Z0-9]+)', proveedor_text, re.IGNORECASE)
            if rfc_match:
                data["proveedor"]["rfc"] = rfc_match.group(1).strip()
        
        # Extraer número de factura
        invoice_patterns = [
            r'(?:factura|invoice)\s*(?:no|numero|number|#)?\s*:?\s*([A-Z0-9\-]+)',
            r'(?:no|numero|number|#)\s*:?\s*([A-Z0-9\-]+)',
        ]
        for pattern in invoice_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                data["numero_factura"] = match.group(1).strip()
                break
        
        # Extraer fecha
        date_patterns = [
            r'(?:fecha|date)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                data["fecha"] = match.group(1).strip()
                break
        
        # Extraer totales
        total_patterns = [
            r'total\s*:?\s*\$?\s*([\d,]+\.?\d*)',
            r'total\s+[\$]?\s*([\d,]+\.?\d*)',
        ]
        for pattern in total_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                data["total"] = InvoiceParser._extract_amount(match.group(1))
                break
        
        return data
    
    @staticmethod
    def parse_invoice_from_response(response: Dict[str, Any], raw_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Parsea datos de factura desde respuesta de Textract.
        
        ¿Qué hace la función?
        Procesa la respuesta completa de Textract analyze_document para extraer
        datos estructurados de factura: cliente, proveedor, productos, número,
        fecha y totales. Usa Key-Value pairs y tablas, con fallback a regex
        en texto plano si es necesario.
        
        ¿Qué parámetros recibe y de qué tipo?
        - response (Dict[str, Any]): Respuesta completa de Textract analyze_document
        - raw_text (Optional[str]): Texto plano del documento para fallback
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con datos de factura:
          - cliente: {nombre, direccion, rfc}
          - proveedor: {nombre, direccion, rfc}
          - numero_factura: Número de factura
          - fecha: Fecha de la factura
          - productos: Lista de productos
          - subtotal: Subtotal
          - iva: IVA
          - total: Total
        """
        invoice_data = {
            "cliente": {},
            "proveedor": {},
            "numero_factura": None,
            "fecha": None,
            "productos": [],
            "subtotal": None,
            "iva": None,
            "total": None
        }
        
        try:
            # Extraer pares clave-valor de FORMS
            key_value_pairs_list = InvoiceParser.extract_key_value_pairs(response)
            logger.info(f"Extracted {len(key_value_pairs_list)} key-value pairs")
            
            # Extraer tablas para productos
            tables = InvoiceParser.extract_tables(response)
            
            # Rastrear campos ya asignados para evitar duplicados
            cliente_nombre_assigned = False
            cliente_direccion_assigned = False
            cliente_rfc_assigned = False
            proveedor_nombre_assigned = False
            proveedor_direccion_assigned = False
            proveedor_rfc_assigned = False
            
            # Rastrear si hemos visto secciones "DATOS DEL CLIENTE" o "DATOS DEL PROVEEDOR"
            in_cliente_section = False
            in_proveedor_section = False
            
            # Parsear pares clave-valor en orden (arriba a abajo)
            for kv_pair in key_value_pairs_list:
                key = kv_pair['key']
                value_str = str(kv_pair['value']).strip()
                original_key = kv_pair.get('original_key', key)
                key_lower = key.lower()
                
                # Verificar si estamos entrando a una sección
                if 'datos del cliente' in original_key.lower() or ('cliente' in original_key.lower() and 'datos' in original_key.lower()):
                    in_cliente_section = True
                    in_proveedor_section = False
                    logger.debug("Entering CLIENTE section")
                elif 'datos del proveedor' in original_key.lower() or ('proveedor' in original_key.lower() and 'datos' in original_key.lower()):
                    in_proveedor_section = True
                    in_cliente_section = False
                    logger.debug("Entering PROVEEDOR section")
                
                # RFC - asignar basado en contexto de sección u orden
                if 'rfc' in key_lower:
                    if in_proveedor_section or (not in_cliente_section and not proveedor_rfc_assigned and cliente_rfc_assigned):
                        if not proveedor_rfc_assigned:
                            invoice_data["proveedor"]["rfc"] = value_str
                            proveedor_rfc_assigned = True
                            logger.debug(f"Assigned RFC to PROVEEDOR: {value_str}")
                    else:
                        if not cliente_rfc_assigned:
                            invoice_data["cliente"]["rfc"] = value_str
                            cliente_rfc_assigned = True
                            logger.debug(f"Assigned RFC to CLIENTE: {value_str}")
                
                # Palabras clave de sección cliente
                elif any(kw in key_lower for kw in ['cliente', 'client', 'customer', 'comprador']):
                    if 'nombre' in key_lower or 'name' in key_lower:
                        invoice_data["cliente"]["nombre"] = value_str
                        cliente_nombre_assigned = True
                    elif 'direccion' in key_lower or 'address' in key_lower or 'dirección' in key_lower:
                        invoice_data["cliente"]["direccion"] = value_str
                        cliente_direccion_assigned = True
                    elif 'rfc' in key_lower:
                        invoice_data["cliente"]["rfc"] = value_str
                        cliente_rfc_assigned = True
                    else:
                        if not cliente_nombre_assigned:
                            invoice_data["cliente"]["nombre"] = value_str
                            cliente_nombre_assigned = True
                
                # Sección proveedor
                elif any(kw in key_lower for kw in ['proveedor', 'provider', 'vendor', 'supplier', 'vendedor']):
                    if 'nombre' in key_lower or 'name' in key_lower:
                        invoice_data["proveedor"]["nombre"] = value_str
                        proveedor_nombre_assigned = True
                    elif 'direccion' in key_lower or 'address' in key_lower or 'dirección' in key_lower:
                        invoice_data["proveedor"]["direccion"] = value_str
                        proveedor_direccion_assigned = True
                    elif 'rfc' in key_lower:
                        invoice_data["proveedor"]["rfc"] = value_str
                        proveedor_rfc_assigned = True
                    else:
                        if not proveedor_nombre_assigned:
                            invoice_data["proveedor"]["nombre"] = value_str
                            proveedor_nombre_assigned = True
                
                # Genérico "Nombre:" - asignar basado en contexto de sección u orden
                elif 'nombre' in key_lower or 'name' in key_lower:
                    if in_proveedor_section:
                        if not proveedor_nombre_assigned:
                            invoice_data["proveedor"]["nombre"] = value_str
                            proveedor_nombre_assigned = True
                            logger.debug(f"Assigned Nombre to PROVEEDOR: {value_str}")
                    elif in_cliente_section or not cliente_nombre_assigned:
                        if not cliente_nombre_assigned:
                            invoice_data["cliente"]["nombre"] = value_str
                            cliente_nombre_assigned = True
                            logger.debug(f"Assigned Nombre to CLIENTE: {value_str}")
                    else:
                        if not proveedor_nombre_assigned:
                            invoice_data["proveedor"]["nombre"] = value_str
                            proveedor_nombre_assigned = True
                            logger.debug(f"Assigned Nombre to PROVEEDOR (by order): {value_str}")
                
                # Genérico "Dirección:" - asignar basado en contexto de sección u orden
                elif 'direccion' in key_lower or 'address' in key_lower or 'dirección' in key_lower:
                    if in_proveedor_section:
                        if not proveedor_direccion_assigned:
                            invoice_data["proveedor"]["direccion"] = value_str
                            proveedor_direccion_assigned = True
                            logger.debug(f"Assigned Direccion to PROVEEDOR: {value_str}")
                    elif in_cliente_section or not cliente_direccion_assigned:
                        if not cliente_direccion_assigned:
                            invoice_data["cliente"]["direccion"] = value_str
                            cliente_direccion_assigned = True
                            logger.debug(f"Assigned Direccion to CLIENTE: {value_str}")
                    else:
                        if not proveedor_direccion_assigned:
                            invoice_data["proveedor"]["direccion"] = value_str
                            proveedor_direccion_assigned = True
                            logger.debug(f"Assigned Direccion to PROVEEDOR (by order): {value_str}")
                
                # Número de factura
                elif any(kw in key_lower for kw in ['número de factura', 'numero de factura', 'invoice number', 'factura no', 'factura numero', 'invoice no']):
                    invoice_data["numero_factura"] = value_str
                
                # Fecha
                elif any(kw in key_lower for kw in ['fecha', 'date', 'fecha de factura', 'invoice date']):
                    invoice_data["fecha"] = value_str
                
                # Totales
                elif 'total' in key_lower and 'subtotal' not in key_lower and 'iva' not in key_lower:
                    invoice_data["total"] = InvoiceParser._extract_amount(value_str)
                elif 'subtotal' in key_lower:
                    invoice_data["subtotal"] = InvoiceParser._extract_amount(value_str)
                elif 'iva' in key_lower or 'tax' in key_lower or 'impuesto' in key_lower:
                    invoice_data["iva"] = InvoiceParser._extract_amount(value_str)
            
            # Parsear productos desde tablas
            products = InvoiceParser.parse_products_from_tables(tables)
            if products:
                invoice_data["productos"] = products
                logger.info(f"Extracted {len(products)} products from tables")
                for idx, prod in enumerate(products, 1):
                    logger.info(f"Product {idx}: cantidad={prod.get('cantidad')}, nombre={prod.get('nombre')}, precio_unitario={prod.get('precio_unitario')}, total={prod.get('total')}")
            else:
                logger.warning("No products extracted from tables")
            
            # Log de datos extraídos para debugging
            logger.info(f"Extracted cliente: {invoice_data.get('cliente')}")
            logger.info(f"Extracted proveedor: {invoice_data.get('proveedor')}")
            
            # Fallback: intentar extraer desde texto plano si key-value pairs no funcionaron
            if raw_text:
                if not invoice_data.get("cliente") or not invoice_data["cliente"].get("nombre"):
                    fallback_data = InvoiceParser.parse_invoice_from_text(raw_text)
                    if fallback_data.get("cliente") and fallback_data["cliente"].get("nombre"):
                        if not invoice_data.get("cliente"):
                            invoice_data["cliente"] = {}
                        invoice_data["cliente"].update(fallback_data["cliente"])
                
                if not invoice_data.get("proveedor") or not invoice_data["proveedor"].get("nombre"):
                    fallback_data = InvoiceParser.parse_invoice_from_text(raw_text)
                    if fallback_data.get("proveedor") and fallback_data["proveedor"].get("nombre"):
                        if not invoice_data.get("proveedor"):
                            invoice_data["proveedor"] = {}
                        invoice_data["proveedor"].update(fallback_data["proveedor"])
                
                # Otros campos fallback
                if not invoice_data.get("numero_factura"):
                    fallback_data = InvoiceParser.parse_invoice_from_text(raw_text)
                    if fallback_data.get("numero_factura"):
                        invoice_data["numero_factura"] = fallback_data["numero_factura"]
                    if fallback_data.get("fecha"):
                        invoice_data["fecha"] = fallback_data["fecha"]
                    if fallback_data.get("total"):
                        invoice_data["total"] = fallback_data["total"]
            
        except Exception as e:
            logger.error(f"Error parsing invoice from response: {str(e)}")
        
        return invoice_data

