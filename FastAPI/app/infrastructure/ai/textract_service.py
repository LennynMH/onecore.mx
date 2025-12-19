"""AWS Textract service for document analysis."""

import logging
import io
from typing import Optional, Dict, Any, List
from fastapi import UploadFile

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    TEXTRACT_AVAILABLE = True
except ImportError:
    TEXTRACT_AVAILABLE = False
    boto3 = None

from app.core.config import settings

logger = logging.getLogger(__name__)


class TextractService:
    """Service for AWS Textract document analysis."""
    
    def __init__(self):
        """Initialize Textract service."""
        self.textract_client = None
        self.is_configured = False
        
        if not TEXTRACT_AVAILABLE:
            logger.warning("boto3 not available. Textract service will be disabled.")
            return
        
        # Check if AWS credentials are configured
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            try:
                self.textract_client = boto3.client(
                    'textract',
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                    region_name=settings.aws_region
                )
                self.is_configured = True
                logger.info("AWS Textract service initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Textract client: {str(e)}")
                self.is_configured = False
        else:
            logger.warning("AWS credentials not configured. Textract service will be disabled.")
    
    async def analyze_document(
        self,
        file: UploadFile,
        s3_key: Optional[str] = None,
        s3_bucket: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze document using AWS Textract.
        
        Args:
            file: Document file to analyze
            s3_key: S3 key if file is already in S3 (optional, for better performance)
            s3_bucket: S3 bucket name (optional)
            
        Returns:
            Dictionary with:
            - classification: "FACTURA" or "INFORMACIÓN"
            - raw_text: Extracted text from document
            - confidence: Confidence score (0-100)
            - processing_time_ms: Processing time in milliseconds
        """
        if not self.is_configured or not self.textract_client:
            logger.warning("Textract not configured. Returning default classification.")
            return {
                "classification": "INFORMACIÓN",
                "raw_text": "",
                "confidence": 0.0,
                "processing_time_ms": 0,
                "error": "Textract not configured"
            }
        
        import time
        start_time = time.time()
        
        try:
            # Read file content
            file_content = await file.read()
            await file.seek(0)  # Reset for potential reuse
            
            # Use S3 if available (better for large files)
            # For classification, we use simple text detection
            if s3_key and s3_bucket:
                response = self._analyze_from_s3(s3_bucket, s3_key, use_forms=False)
            else:
                # Analyze from bytes (for smaller files)
                response = self._analyze_from_bytes(file_content, use_forms=False)
            
            # Extract text from response
            raw_text = self._extract_text_from_response(response)
            
            # Classify document based on content
            classification = self._classify_document(raw_text)
            
            # Calculate confidence (simplified - could be improved)
            confidence = self._calculate_confidence(response, classification)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            logger.info(f"Document analyzed: {classification} (confidence: {confidence:.2f}%)")
            
            return {
                "classification": classification,
                "raw_text": raw_text,
                "confidence": confidence,
                "processing_time_ms": processing_time_ms,
                "error": None
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            logger.error(f"AWS Textract error ({error_code}): {error_message}")
            return {
                "classification": "INFORMACIÓN",
                "raw_text": "",
                "confidence": 0.0,
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "error": f"AWS Textract error: {error_message}"
            }
        except Exception as e:
            logger.error(f"Error analyzing document with Textract: {str(e)}")
            return {
                "classification": "INFORMACIÓN",
                "raw_text": "",
                "confidence": 0.0,
                "processing_time_ms": int((time.time() - start_time) * 1000),
                "error": f"Error: {str(e)}"
            }
    
    def _analyze_from_s3(self, bucket: str, key: str, use_forms: bool = False) -> Dict[str, Any]:
        """Analyze document from S3."""
        if use_forms:
            # Use analyze_document for forms and tables extraction
            response = self.textract_client.analyze_document(
                Document={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                FeatureTypes=["FORMS", "TABLES"]
            )
        else:
            # Use detect_document_text for simple text extraction
            response = self.textract_client.detect_document_text(
                Document={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                }
            )
        return response
    
    def _analyze_from_bytes(self, file_content: bytes, use_forms: bool = False) -> Dict[str, Any]:
        """Analyze document from bytes."""
        if use_forms:
            # Use analyze_document for forms and tables extraction
            response = self.textract_client.analyze_document(
                Document={
                    'Bytes': file_content
                },
                FeatureTypes=["FORMS", "TABLES"]
            )
        else:
            # Use detect_document_text for simple text extraction
            response = self.textract_client.detect_document_text(
                Document={
                    'Bytes': file_content
                }
            )
        return response
    
    def _extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """Extract text from Textract response."""
        text_blocks = []
        
        if 'Blocks' in response:
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    text_blocks.append(block.get('Text', ''))
        
        extracted_text = ' '.join(text_blocks)
        logger.info(f"Extracted text length: {len(extracted_text)} characters")
        if extracted_text:
            logger.info(f"First 500 chars of extracted text: {extracted_text[:500]}")
        else:
            logger.warning("No text extracted from document - Textract may not have found any text")
        return extracted_text
    
    def _classify_document(self, text: str) -> str:
        """
        Classify document as FACTURA or INFORMACIÓN based on content.
        
        Args:
            text: Extracted text from document
            
        Returns:
            "FACTURA" or "INFORMACIÓN"
        """
        if not text or not text.strip():
            logger.warning("Empty text extracted, classifying as INFORMACIÓN")
            return "INFORMACIÓN"
        
        # Normalize text: lowercase, remove extra spaces, normalize special characters
        import re
        text_normalized = re.sub(r'\s+', ' ', text.lower().strip())
        
        # Keywords that indicate a FACTURA (Invoice)
        # Separadas por importancia para evitar falsos positivos
        
        # Keywords CRÍTICAS (deben estar presentes)
        critical_keywords = [
            'factura', 'invoice', 'recibo', 'receipt', 'bill',
            'número de factura', 'numero de factura', 'invoice number', 'invoice no',
            'factura no', 'factura numero'
        ]
        
        # Keywords IMPORTANTES (indican contexto de factura)
        important_keywords = [
            'cliente', 'client', 'customer',
            'proveedor', 'provider', 'vendor', 'supplier',
            'total', 'subtotal', 'iva', 'tax', 'impuesto',
            'cantidad', 'quantity', 'qty',
            'precio unitario', 'unit price', 'precio', 'unitario',
            'producto', 'product', 'item',
            'rfc', 'tax id', 'cuit'
        ]
        
        # Keywords SECUNDARIAS (comunes, pueden aparecer en otros documentos)
        secondary_keywords = [
            'comprador', 'buyer', 'vendedor', 'seller',
            'taxes', 'qty.', 'cant.', 'articulo', 'article',
            'servicio', 'service',  # Muy común en documentos informativos
            'fecha de factura', 'invoice date', 'date', 'fecha',  # Muy común
            'pago', 'payment', 'metodo de pago', 'payment method',
            'detalle', 'detail', 'concepto', 'concept'
        ]
        
        # Buscar keywords críticas
        found_critical = [kw for kw in critical_keywords if kw in text_normalized]
        
        # Buscar keywords importantes
        found_important = [kw for kw in important_keywords if kw in text_normalized]
        
        # Buscar keywords secundarias
        found_secondary = [kw for kw in secondary_keywords if kw in text_normalized]
        
        # Calcular score con pesos
        # Críticas: 3 puntos cada una
        # Importantes: 2 puntos cada una
        # Secundarias: 1 punto cada una
        critical_score = len(found_critical) * 3
        important_score = len(found_important) * 2
        secondary_score = len(found_secondary) * 1
        total_score = critical_score + important_score + secondary_score
        
        # Contar total de keywords encontradas (para logging)
        total_keywords_found = len(found_critical) + len(found_important) + len(found_secondary)
        all_found_keywords = found_critical + found_important + found_secondary
        
        # Log classification details for debugging
        logger.info(f"Classification analysis: {total_keywords_found} keywords found")
        logger.info(f"  Critical ({len(found_critical)}): {', '.join(found_critical[:5])}")
        logger.info(f"  Important ({len(found_important)}): {', '.join(found_important[:5])}")
        logger.info(f"  Secondary ({len(found_secondary)}): {', '.join(found_secondary[:5])}")
        logger.info(f"  Weighted score: {total_score} (critical: {critical_score}, important: {important_score}, secondary: {secondary_score})")
        
        # Regla de clasificación mejorada (más estricta para evitar falsos positivos):
        # 1. Si hay al menos 1 keyword crítica Y al menos 2 keywords importantes Y score total >= 12 → FACTURA
        # 2. Si hay al menos 2 keywords críticas Y score total >= 10 → FACTURA
        # 3. Si hay al menos 4 keywords importantes Y score total >= 14 → FACTURA
        # 4. Si score total >= 16 → FACTURA
        # 5. De lo contrario → INFORMACIÓN
        
        is_factura = False
        
        if len(found_critical) >= 1 and len(found_important) >= 2 and total_score >= 12:
            is_factura = True
            logger.info(f"Document classified as FACTURA (rule 1: 1+ critical + 2+ important + score >= 12)")
        elif len(found_critical) >= 2 and total_score >= 10:
            is_factura = True
            logger.info(f"Document classified as FACTURA (rule 2: 2+ critical keywords + score >= 10)")
        elif len(found_important) >= 4 and total_score >= 14:
            is_factura = True
            logger.info(f"Document classified as FACTURA (rule 3: 4+ important keywords + score >= 14)")
        elif total_score >= 16:
            is_factura = True
            logger.info(f"Document classified as FACTURA (rule 4: total score >= 16)")
        else:
            logger.info(f"Document classified as INFORMACIÓN (score: {total_score}, thresholds not met)")
        
        if is_factura:
            return "FACTURA"
        else:
            return "INFORMACIÓN"
    
    async def extract_invoice_data(
        self,
        file: UploadFile,
        s3_key: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from an invoice document.
        
        Args:
            file: Document file
            s3_key: S3 key if file is in S3
            s3_bucket: S3 bucket name
            raw_text: Previously extracted text (optional, to avoid re-extraction)
            
        Returns:
            Dictionary with extracted invoice data
        """
        if not self.is_configured or not self.textract_client:
            logger.warning("Textract not configured. Cannot extract invoice data.")
            return {}
        
        try:
            # Read file content if needed
            file_content = None
            if not raw_text:
                file_content = await file.read()
                await file.seek(0)
            
            # Use analyze_document with FORMS and TABLES for better extraction
            if s3_key and s3_bucket:
                response = self._analyze_from_s3(s3_bucket, s3_key, use_forms=True)
            elif file_content:
                response = self._analyze_from_bytes(file_content, use_forms=True)
            else:
                logger.warning("Cannot extract invoice data: no file content or S3 key")
                return {}
            
            # Extract structured data
            invoice_data = self._parse_invoice_from_response(response, raw_text)
            
            logger.info(f"Invoice data extracted: {len(invoice_data)} fields found")
            return invoice_data
            
        except Exception as e:
            logger.error(f"Error extracting invoice data: {str(e)}")
            return {}
    
    def _parse_invoice_from_response(self, response: Dict[str, Any], raw_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse invoice data from Textract response.
        
        Args:
            response: Textract analyze_document response
            raw_text: Optional raw text for fallback parsing
            
        Returns:
            Dictionary with invoice data
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
            # Extract Key-Value pairs from FORMS (now returns ordered list)
            key_value_pairs_list = self._extract_key_value_pairs(response)
            logger.info(f"Extracted {len(key_value_pairs_list)} key-value pairs")
            
            # Extract tables for products
            tables = self._extract_tables(response)
            
            # Track which fields we've already assigned to avoid duplicates
            cliente_nombre_assigned = False
            cliente_direccion_assigned = False
            cliente_rfc_assigned = False
            proveedor_nombre_assigned = False
            proveedor_direccion_assigned = False
            proveedor_rfc_assigned = False
            
            # Track if we've seen "DATOS DEL CLIENTE" or "DATOS DEL PROVEEDOR" sections
            in_cliente_section = False
            in_proveedor_section = False
            
            # Parse key-value pairs in order (top to bottom)
            for kv_pair in key_value_pairs_list:
                key = kv_pair['key']
                value_str = str(kv_pair['value']).strip()
                original_key = kv_pair.get('original_key', key)
                key_lower = key.lower()
                
                # Check if we're entering a section
                if 'datos del cliente' in original_key.lower() or ('cliente' in original_key.lower() and 'datos' in original_key.lower()):
                    in_cliente_section = True
                    in_proveedor_section = False
                    logger.debug("Entering CLIENTE section")
                elif 'datos del proveedor' in original_key.lower() or ('proveedor' in original_key.lower() and 'datos' in original_key.lower()):
                    in_proveedor_section = True
                    in_cliente_section = False
                    logger.debug("Entering PROVEEDOR section")
                
                # RFC - assign based on section context or order
                if 'rfc' in key_lower:
                    if in_proveedor_section or (not in_cliente_section and proveedor_rfc_assigned == False and cliente_rfc_assigned):
                        # If we're in proveedor section, or if cliente RFC already assigned, this is proveedor
                        if not proveedor_rfc_assigned:
                            invoice_data["proveedor"]["rfc"] = value_str
                            proveedor_rfc_assigned = True
                            logger.debug(f"Assigned RFC to PROVEEDOR: {value_str}")
                    else:
                        # Otherwise, assign to cliente
                        if not cliente_rfc_assigned:
                            invoice_data["cliente"]["rfc"] = value_str
                            cliente_rfc_assigned = True
                            logger.debug(f"Assigned RFC to CLIENTE: {value_str}")
                
                # Cliente section keywords
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
                
                # Proveedor section
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
                
                # Generic "Nombre:" - assign based on section context or order
                elif 'nombre' in key_lower or 'name' in key_lower:
                    if in_proveedor_section:
                        # We're in proveedor section
                        if not proveedor_nombre_assigned:
                            invoice_data["proveedor"]["nombre"] = value_str
                            proveedor_nombre_assigned = True
                            logger.debug(f"Assigned Nombre to PROVEEDOR: {value_str}")
                    elif in_cliente_section or not cliente_nombre_assigned:
                        # We're in cliente section or haven't assigned cliente yet
                        if not cliente_nombre_assigned:
                            invoice_data["cliente"]["nombre"] = value_str
                            cliente_nombre_assigned = True
                            logger.debug(f"Assigned Nombre to CLIENTE: {value_str}")
                    else:
                        # Cliente already assigned, this must be proveedor
                        if not proveedor_nombre_assigned:
                            invoice_data["proveedor"]["nombre"] = value_str
                            proveedor_nombre_assigned = True
                            logger.debug(f"Assigned Nombre to PROVEEDOR (by order): {value_str}")
                
                # Generic "Dirección:" - assign based on section context or order
                elif 'direccion' in key_lower or 'address' in key_lower or 'dirección' in key_lower:
                    if in_proveedor_section:
                        # We're in proveedor section
                        if not proveedor_direccion_assigned:
                            invoice_data["proveedor"]["direccion"] = value_str
                            proveedor_direccion_assigned = True
                            logger.debug(f"Assigned Direccion to PROVEEDOR: {value_str}")
                    elif in_cliente_section or not cliente_direccion_assigned:
                        # We're in cliente section or haven't assigned cliente yet
                        if not cliente_direccion_assigned:
                            invoice_data["cliente"]["direccion"] = value_str
                            cliente_direccion_assigned = True
                            logger.debug(f"Assigned Direccion to CLIENTE: {value_str}")
                    else:
                        # Cliente already assigned, this must be proveedor
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
                    invoice_data["total"] = self._extract_amount(value_str)
                elif 'subtotal' in key_lower:
                    invoice_data["subtotal"] = self._extract_amount(value_str)
                elif 'iva' in key_lower or 'tax' in key_lower or 'impuesto' in key_lower:
                    invoice_data["iva"] = self._extract_amount(value_str)
            
            # Parse products from tables
            products = self._parse_products_from_tables(tables)
            if products:
                invoice_data["productos"] = products
                logger.info(f"Extracted {len(products)} products from tables")
                for idx, prod in enumerate(products, 1):
                    logger.info(f"Product {idx}: cantidad={prod.get('cantidad')}, nombre={prod.get('nombre')}, precio_unitario={prod.get('precio_unitario')}, total={prod.get('total')}")
            else:
                logger.warning("No products extracted from tables")
            
            # Log extracted data for debugging
            logger.info(f"Extracted cliente: {invoice_data.get('cliente')}")
            logger.info(f"Extracted proveedor: {invoice_data.get('proveedor')}")
            
            # Fallback: try to extract from raw text if key-value pairs didn't work
            # Especially for cliente and proveedor which might not be in key-value format
            if raw_text:
                # If cliente or proveedor are empty, try to extract from raw text
                if not invoice_data.get("cliente") or not invoice_data["cliente"].get("nombre"):
                    fallback_data = self._parse_invoice_from_text(raw_text)
                    if fallback_data.get("cliente") and fallback_data["cliente"].get("nombre"):
                        if not invoice_data.get("cliente"):
                            invoice_data["cliente"] = {}
                        invoice_data["cliente"].update(fallback_data["cliente"])
                
                if not invoice_data.get("proveedor") or not invoice_data["proveedor"].get("nombre"):
                    fallback_data = self._parse_invoice_from_text(raw_text)
                    if fallback_data.get("proveedor") and fallback_data["proveedor"].get("nombre"):
                        if not invoice_data.get("proveedor"):
                            invoice_data["proveedor"] = {}
                        invoice_data["proveedor"].update(fallback_data["proveedor"])
                
                # Other fields fallback
                if not invoice_data.get("numero_factura"):
                    fallback_data = self._parse_invoice_from_text(raw_text)
                    if fallback_data.get("numero_factura"):
                        invoice_data["numero_factura"] = fallback_data["numero_factura"]
                    if fallback_data.get("fecha"):
                        invoice_data["fecha"] = fallback_data["fecha"]
                    if fallback_data.get("total"):
                        invoice_data["total"] = fallback_data["total"]
            
        except Exception as e:
            logger.error(f"Error parsing invoice from response: {str(e)}")
        
        return invoice_data
    
    def _extract_key_value_pairs(self, response: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract Key-Value pairs from Textract FORMS response.
        Returns a list to preserve order and allow duplicates.
        """
        key_value_pairs_list = []
        
        if 'Blocks' not in response:
            return key_value_pairs_list
        
        # Build relationships map
        relationships = {}
        blocks_map = {}
        
        for block in response['Blocks']:
            block_id = block.get('Id')
            if block_id:
                blocks_map[block_id] = block
                if 'Relationships' in block:
                    relationships[block_id] = block['Relationships']
        
        # Find KEY-VALUE pairs and preserve order
        for block in response['Blocks']:
            if block.get('BlockType') == 'KEY_VALUE_SET':
                entity_type = block.get('EntityTypes', [])
                if 'KEY' in entity_type:
                    # This is a KEY block
                    key_text = self._get_text_from_block(block, blocks_map, relationships)
                    # Find associated VALUE
                    value_text = self._get_value_from_key(block, blocks_map, relationships)
                    if key_text and value_text:
                        # Get Y position to preserve order (top to bottom)
                        y_position = block.get('Geometry', {}).get('BoundingBox', {}).get('Top', 0)
                        key_value_pairs_list.append({
                            'key': key_text.lower(),
                            'value': value_text,
                            'y_position': y_position,
                            'original_key': key_text
                        })
                        logger.debug(f"Found key-value pair: '{key_text}' = '{value_text}' (Y: {y_position:.4f})")
        
        # Sort by Y position (top to bottom) to preserve document order
        key_value_pairs_list.sort(key=lambda x: x['y_position'])
        
        logger.info(f"Total key-value pairs extracted: {len(key_value_pairs_list)}")
        return key_value_pairs_list
    
    def _get_text_from_block(self, block: Dict[str, Any], blocks_map: Dict, relationships: Dict) -> str:
        """Get text from a block by following relationships."""
        text_parts = []
        
        if 'Relationships' in block:
            for rel in block['Relationships']:
                if rel.get('Type') == 'CHILD':
                    for child_id in rel.get('Ids', []):
                        child = blocks_map.get(child_id)
                        if child and child.get('BlockType') == 'WORD':
                            text_parts.append(child.get('Text', ''))
        
        return ' '.join(text_parts).strip()
    
    def _get_value_from_key(self, key_block: Dict[str, Any], blocks_map: Dict, relationships: Dict) -> str:
        """Get value associated with a key block."""
        # In Textract, a KEY block has a relationship of type "VALUE" that points to the VALUE block ID
        if 'Relationships' in key_block:
            for rel in key_block['Relationships']:
                if rel.get('Type') == 'VALUE':
                    # Get the VALUE block IDs
                    for value_id in rel.get('Ids', []):
                        value_block = blocks_map.get(value_id)
                        if value_block and value_block.get('BlockType') == 'KEY_VALUE_SET':
                            entity_type = value_block.get('EntityTypes', [])
                            if 'VALUE' in entity_type:
                                return self._get_text_from_block(value_block, blocks_map, relationships)
        
        return ""
    
    def _extract_tables(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract tables from Textract response."""
        tables = []
        
        if 'Blocks' not in response:
            return tables
        
        # Find TABLE blocks
        for block in response['Blocks']:
            if block.get('BlockType') == 'TABLE':
                table_data = self._parse_table_block(block, response.get('Blocks', []))
                if table_data:
                    tables.append(table_data)
        
        return tables
    
    def _parse_table_block(self, table_block: Dict[str, Any], all_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse a single table block."""
        # Build blocks map
        blocks_map = {block.get('Id'): block for block in all_blocks if block.get('Id')}
        
        # Get cells from table
        cells = []
        if 'Relationships' in table_block:
            for rel in table_block['Relationships']:
                if rel.get('Type') == 'CHILD':
                    for cell_id in rel.get('Ids', []):
                        cell = blocks_map.get(cell_id)
                        if cell and cell.get('BlockType') == 'CELL':
                            cell_text = self._get_text_from_cell(cell, blocks_map)
                            row_index = cell.get('RowIndex', 0)
                            col_index = cell.get('ColumnIndex', 0)
                            cells.append({
                                'row': row_index,
                                'col': col_index,
                                'text': cell_text
                            })
        
        return {'cells': cells}
    
    def _get_text_from_cell(self, cell: Dict[str, Any], blocks_map: Dict) -> str:
        """Get text from a table cell."""
        text_parts = []
        
        if 'Relationships' in cell:
            for rel in cell['Relationships']:
                if rel.get('Type') == 'CHILD':
                    for child_id in rel.get('Ids', []):
                        child = blocks_map.get(child_id)
                        if child:
                            if child.get('BlockType') == 'WORD':
                                text_parts.append(child.get('Text', ''))
                            elif child.get('BlockType') == 'SELECTION_ELEMENT':
                                # Checkbox or selection
                                if child.get('SelectionStatus') == 'SELECTED':
                                    text_parts.append('X')
        
        return ' '.join(text_parts).strip()
    
    def _parse_products_from_tables(self, tables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse products from table data by identifying headers first."""
        products = []
        
        for table in tables:
            cells = table.get('cells', [])
            if not cells:
                continue
            
            # Group cells by row
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
            
            # Find header row (usually row 1, but could be row 0)
            header_row_num = None
            column_mapping = {}  # Maps column index to field name
            
            # Try to find header row
            for row_num in sorted(rows.keys()):
                row_data = rows[row_num]
                header_texts = [rows[row_num].get(col, '').lower() for col in sorted(row_data.keys())]
                header_text = ' '.join(header_texts)
                
                # Check if this looks like a header row
                if any(keyword in header_text for keyword in ['cantidad', 'producto', 'precio', 'unitario', 'total', 'descripcion']):
                    header_row_num = row_num
                    # Map columns based on header content
                    for col_num in sorted(row_data.keys()):
                        header_cell = row_data[col_num].lower().strip()
                        
                        if 'cantidad' in header_cell or 'qty' in header_cell:
                            column_mapping[col_num] = 'cantidad'
                        elif 'producto' in header_cell or 'descripcion' in header_cell or 'nombre' in header_cell or 'item' in header_cell:
                            column_mapping[col_num] = 'nombre'
                        elif 'precio' in header_cell and 'unitario' in header_cell:
                            column_mapping[col_num] = 'precio_unitario'
                        elif 'precio' in header_cell and 'unitario' not in header_cell:
                            # Could be precio unitario or total, check position
                            if not column_mapping.get('precio_unitario'):
                                column_mapping[col_num] = 'precio_unitario'
                        elif 'total' in header_cell and 'precio' not in header_cell:
                            column_mapping[col_num] = 'total'
                    
                    break
            
            # If no header found, use default mapping (assume order: cantidad, nombre, precio_unitario, total)
            if not header_row_num:
                header_row_num = min(rows.keys()) if rows else 1
                # Default mapping: assume first numeric is cantidad, last two amounts are precio and total
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
            
            # Parse data rows
            for row_num in sorted(rows.keys()):
                if row_num == header_row_num:  # Skip header row
                    continue
                
                row_data = rows[row_num]
                product = {}
                
                # Extract data based on column mapping
                for col_num in sorted(row_data.keys()):
                    text = row_data[col_num].strip()
                    if not text:
                        continue
                    
                    field_name = column_mapping.get(col_num)
                    if field_name:
                        if field_name in ['precio_unitario', 'total']:
                            # Extract amount, preserving format
                            amount = self._extract_amount(text)
                            if amount:
                                product[field_name] = amount
                            else:
                                # If extraction fails, use original text
                                product[field_name] = text
                        else:
                            product[field_name] = text
                    else:
                        # Fallback: try to identify by content if no mapping
                        if not product.get("cantidad") and self._is_numeric(text) and not ('$' in text or self._is_amount(text)):
                            product["cantidad"] = text
                        elif not product.get("nombre") and not self._is_amount(text):
                            product["nombre"] = text
                        elif not product.get("precio_unitario") and ('$' in text or self._is_amount(text)):
                            amount = self._extract_amount(text)
                            if amount:
                                product["precio_unitario"] = amount
                        elif not product.get("total") and ('$' in text or self._is_amount(text)):
                            amount = self._extract_amount(text)
                            if amount:
                                product["total"] = amount
                
                # Only add product if it has at least nombre or cantidad
                if product.get("nombre") or product.get("cantidad"):
                    products.append(product)
        
        return products
    
    def _is_numeric(self, text: str) -> bool:
        """Check if text is numeric."""
        try:
            float(text.replace(',', '').replace('$', '').strip())
            return True
        except:
            return False
    
    def _is_amount(self, text: str) -> bool:
        """Check if text looks like an amount."""
        return '$' in text or any(char.isdigit() for char in text)
    
    def _extract_amount(self, text: str) -> Optional[str]:
        """Extract amount from text (removes currency symbols, keeps numbers)."""
        if not text:
            return None
        
        # Remove currency symbols and extract numbers
        import re
        # Match numbers with optional decimals
        match = re.search(r'[\d,]+\.?\d*', text.replace('$', '').replace(',', ''))
        if match:
            return match.group(0)
        return None
    
    def _parse_invoice_from_text(self, raw_text: str) -> Dict[str, Any]:
        """Fallback: Parse invoice data from raw text using regex patterns."""
        import re
        data = {
            "cliente": {},
            "proveedor": {}
        }
        
        # Extract cliente (client) - look for "DATOS DEL CLIENTE" section
        cliente_section_pattern = r'DATOS\s+DEL\s+CLIENTE[^\n]*\n(.*?)(?=DATOS\s+DEL\s+PROVEEDOR|DETALLE|$)'
        cliente_match = re.search(cliente_section_pattern, raw_text, re.IGNORECASE | re.DOTALL)
        if cliente_match:
            cliente_text = cliente_match.group(1)
            
            # Extract nombre
            nombre_match = re.search(r'Nombre\s*:?\s*([^\n]+)', cliente_text, re.IGNORECASE)
            if nombre_match:
                data["cliente"]["nombre"] = nombre_match.group(1).strip()
            
            # Extract dirección
            direccion_match = re.search(r'Direcci[oó]n\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=RFC|$)', cliente_text, re.IGNORECASE)
            if direccion_match:
                direccion = direccion_match.group(1).strip()
                # Clean up multiple lines
                direccion = ' '.join(line.strip() for line in direccion.split('\n') if line.strip())
                data["cliente"]["direccion"] = direccion
            
            # Extract RFC
            rfc_match = re.search(r'RFC\s*:?\s*([A-Z0-9]+)', cliente_text, re.IGNORECASE)
            if rfc_match:
                data["cliente"]["rfc"] = rfc_match.group(1).strip()
        
        # Extract proveedor (provider) - look for "DATOS DEL PROVEEDOR" section
        proveedor_section_pattern = r'DATOS\s+DEL\s+PROVEEDOR[^\n]*\n(.*?)(?=DETALLE|TOTAL|$)'
        proveedor_match = re.search(proveedor_section_pattern, raw_text, re.IGNORECASE | re.DOTALL)
        if proveedor_match:
            proveedor_text = proveedor_match.group(1)
            
            # Extract nombre
            nombre_match = re.search(r'Nombre\s*:?\s*([^\n]+)', proveedor_text, re.IGNORECASE)
            if nombre_match:
                data["proveedor"]["nombre"] = nombre_match.group(1).strip()
            
            # Extract dirección
            direccion_match = re.search(r'Direcci[oó]n\s*:?\s*([^\n]+(?:\n[^\n]+)*?)(?=RFC|$)', proveedor_text, re.IGNORECASE)
            if direccion_match:
                direccion = direccion_match.group(1).strip()
                # Clean up multiple lines
                direccion = ' '.join(line.strip() for line in direccion.split('\n') if line.strip())
                data["proveedor"]["direccion"] = direccion
            
            # Extract RFC
            rfc_match = re.search(r'RFC\s*:?\s*([A-Z0-9]+)', proveedor_text, re.IGNORECASE)
            if rfc_match:
                data["proveedor"]["rfc"] = rfc_match.group(1).strip()
        
        # Extract invoice number
        invoice_patterns = [
            r'(?:factura|invoice)\s*(?:no|numero|number|#)?\s*:?\s*([A-Z0-9\-]+)',
            r'(?:no|numero|number|#)\s*:?\s*([A-Z0-9\-]+)',
        ]
        for pattern in invoice_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                data["numero_factura"] = match.group(1).strip()
                break
        
        # Extract date
        date_patterns = [
            r'(?:fecha|date)\s*:?\s*(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
            r'(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                data["fecha"] = match.group(1).strip()
                break
        
        # Extract totals
        total_patterns = [
            r'total\s*:?\s*\$?\s*([\d,]+\.?\d*)',
            r'total\s+[\$]?\s*([\d,]+\.?\d*)',
        ]
        for pattern in total_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                data["total"] = self._extract_amount(match.group(1))
                break
        
        return data
    
    async def extract_information_data(
        self,
        file: UploadFile,
        s3_key: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured data from an information document.
        
        Args:
            file: Document file
            s3_key: S3 key if file is in S3
            s3_bucket: S3 bucket name
            raw_text: Previously extracted text (optional)
            
        Returns:
            Dictionary with extracted information data
        """
        information_data = {
            "descripcion": None,
            "resumen": None,
            "sentimiento": None
        }
        
        try:
            # Get raw text if not provided
            if not raw_text:
                if s3_key and s3_bucket:
                    response = self._analyze_from_s3(s3_bucket, s3_key, use_forms=False)
                else:
                    file_content = await file.read()
                    await file.seek(0)
                    response = self._analyze_from_bytes(file_content, use_forms=False)
                raw_text = self._extract_text_from_response(response)
            
            if not raw_text:
                return information_data
            
            # Extract description (first paragraph or first 200 chars)
            paragraphs = [p.strip() for p in raw_text.split('\n') if p.strip()]
            if paragraphs:
                information_data["descripcion"] = paragraphs[0][:500] if len(paragraphs[0]) > 500 else paragraphs[0]
            
            # Generate summary (first 3 paragraphs or first 500 chars)
            if len(paragraphs) >= 3:
                information_data["resumen"] = ' '.join(paragraphs[:3])[:500]
            elif paragraphs:
                information_data["resumen"] = raw_text[:500]
            
            # Sentiment analysis will be done with OpenAI (if configured)
            # For now, set as neutral
            information_data["sentimiento"] = "neutral"
            
            logger.info(f"Information data extracted: description={bool(information_data['descripcion'])}, resumen={bool(information_data['resumen'])}")
            
        except Exception as e:
            logger.error(f"Error extracting information data: {str(e)}")
        
        return information_data
    
    def _calculate_confidence(self, response: Dict[str, Any], classification: str) -> float:
        """
        Calculate confidence score for classification.
        
        Args:
            response: Textract response
            classification: Classification result
            
        Returns:
            Confidence score (0-100)
        """
        if 'Blocks' not in response or not response['Blocks']:
            return 0.0
        
        # Count total blocks
        total_blocks = len([b for b in response['Blocks'] if b.get('BlockType') == 'LINE'])
        
        if total_blocks == 0:
            return 0.0
        
        # Simple confidence based on number of text blocks found
        # More blocks = higher confidence
        confidence = min(100.0, (total_blocks / 10.0) * 100.0)
        
        return round(confidence, 2)

