"""
AWS Textract service for document analysis.

Refactorización con Auto (Claude/ChatGPT) - PARTE 3.1

¿Qué hace este módulo?
Proporciona servicios para análisis de documentos usando AWS Textract,
incluyendo clasificación automática y extracción de datos estructurados.
Esta refactorización utiliza InvoiceParser para mejorar la modularidad.

¿Qué clases contiene?
- TextractService: Servicio principal para análisis de documentos con Textract
"""

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
from app.infrastructure.ai.parsers import InvoiceParser

logger = logging.getLogger(__name__)


class TextractService:
    """Service for AWS Textract document analysis."""
    
    def __init__(self):
        """
        Inicializa el servicio de AWS Textract.
        
        ¿Qué hace la función?
        Configura el cliente de AWS Textract usando las credenciales de settings.
        Si las credenciales no están disponibles, el servicio queda deshabilitado
        pero no lanza errores (permite funcionamiento sin Textract).
        
        ¿Qué parámetros recibe y de qué tipo?
        - Ninguno
        
        ¿Qué dato regresa y de qué tipo?
        - None
        """
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
        Analiza un documento usando AWS Textract para clasificación.
        
        ¿Qué hace la función?
        Extrae texto de un documento usando AWS Textract (desde S3 si está disponible
        o desde bytes), clasifica el documento como FACTURA o INFORMACIÓN basándose
        en el contenido extraído, y retorna el resultado con métricas de confianza.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file (UploadFile): Archivo del documento a analizar (PDF, JPG, PNG)
        - s3_key (str | None): Clave S3 si el archivo ya está en S3 (opcional, mejora rendimiento)
        - s3_bucket (str | None): Nombre del bucket S3 (opcional, requerido si s3_key está presente)
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con:
          - classification (str): Clasificación del documento ("FACTURA" o "INFORMACIÓN")
          - raw_text (str): Texto extraído del documento
          - confidence (float): Puntuación de confianza (0-100)
          - processing_time_ms (int): Tiempo de procesamiento en milisegundos
          - error (str | None): Mensaje de error si ocurrió alguno
        
        Raises:
            No lanza excepciones, retorna error en el diccionario si falla
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
        """
        Analiza un documento desde S3 usando AWS Textract.
        
        ¿Qué hace la función?
        Llama a AWS Textract para analizar un documento que ya está almacenado en S3.
        Puede usar detección simple de texto o análisis avanzado con FORMS y TABLES
        según el parámetro use_forms.
        
        ¿Qué parámetros recibe y de qué tipo?
        - bucket (str): Nombre del bucket S3 donde está el documento
        - key (str): Clave S3 (ruta) del documento
        - use_forms (bool): Si es True, usa analyze_document con FORMS y TABLES; si es False, usa detect_document_text (default: False)
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Respuesta de AWS Textract con bloques de texto y metadatos
        
        Raises:
            ClientError: Si hay un error al comunicarse con AWS Textract
        """
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
        """
        Analiza un documento desde bytes usando AWS Textract.
        
        ¿Qué hace la función?
        Llama a AWS Textract para analizar un documento enviado como bytes en memoria.
        Puede usar detección simple de texto o análisis avanzado con FORMS y TABLES
        según el parámetro use_forms. Útil para archivos pequeños que no están en S3.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file_content (bytes): Contenido del archivo en bytes
        - use_forms (bool): Si es True, usa analyze_document con FORMS y TABLES; si es False, usa detect_document_text (default: False)
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Respuesta de AWS Textract con bloques de texto y metadatos
        
        Raises:
            ClientError: Si hay un error al comunicarse con AWS Textract
        """
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
        """
        Extrae texto de la respuesta de AWS Textract.
        
        ¿Qué hace la función?
        Procesa la respuesta de AWS Textract y extrae todas las líneas de texto
        encontradas en el documento, uniéndolas en un solo string.
        
        ¿Qué parámetros recibe y de qué tipo?
        - response (Dict[str, Any]): Respuesta de AWS Textract con bloques de texto
        
        ¿Qué dato regresa y de qué tipo?
        - str: Texto extraído del documento, unido con espacios
        """
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
        Clasifica un documento como FACTURA o INFORMACIÓN basándose en el contenido.
        
        ¿Qué hace la función?
        Analiza el texto extraído del documento buscando keywords específicas
        categorizadas por importancia (críticas, importantes, secundarias).
        Usa un sistema de puntuación ponderado y reglas estrictas para determinar
        si el documento es una FACTURA o INFORMACIÓN, evitando falsos positivos.
        
        ¿Qué parámetros recibe y de qué tipo?
        - text (str): Texto extraído del documento a clasificar
        
        ¿Qué dato regresa y de qué tipo?
        - str: Clasificación del documento ("FACTURA" o "INFORMACIÓN")
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
        Extrae datos estructurados de un documento de factura.
        
        ¿Qué hace la función?
        Analiza un documento de factura usando AWS Textract con FORMS y TABLES
        para extraer datos estructurados como cliente, proveedor, número de factura,
        productos, totales, etc. Usa InvoiceParser para procesar la respuesta.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file (UploadFile): Archivo del documento de factura
        - s3_key (str | None): Clave S3 si el archivo ya está en S3 (opcional, mejora rendimiento)
        - s3_bucket (str | None): Nombre del bucket S3 (opcional, requerido si s3_key está presente)
        - raw_text (str | None): Texto previamente extraído (opcional, evita re-extracción)
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con datos estructurados de la factura:
          - cliente: Diccionario con nombre, dirección, RFC
          - proveedor: Diccionario con nombre, dirección, RFC
          - numero_factura: Número de factura
          - fecha: Fecha de la factura
          - productos: Lista de productos con cantidad, nombre, precio, total
          - subtotal, iva, total: Totales de la factura
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
        Parsea datos de factura desde respuesta de Textract.
        
        ¿Qué hace la función?
        Delega el parsing de facturas a InvoiceParser, que maneja toda la lógica
        de extracción de datos estructurados desde respuestas de Textract.
        
        ¿Qué parámetros recibe y de qué tipo?
        - response (Dict[str, Any]): Respuesta de Textract analyze_document
        - raw_text (Optional[str]): Texto plano del documento para fallback
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con datos de factura estructurados
        """
        return InvoiceParser.parse_invoice_from_response(response, raw_text)
    
    async def extract_information_data(
        self,
        file: UploadFile,
        s3_key: Optional[str] = None,
        s3_bucket: Optional[str] = None,
        raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extrae datos estructurados de un documento de información.
        
        ¿Qué hace la función?
        Procesa un documento de tipo "INFORMACIÓN" para extraer descripción,
        resumen y análisis de sentimiento. Usa Textract para extraer texto
        y puede integrarse con OpenAI para análisis de sentimiento.
        
        ¿Qué parámetros recibe y de qué tipo?
        - file (UploadFile): Archivo del documento
        - s3_key (Optional[str]): Clave S3 si el archivo está en S3
        - s3_bucket (Optional[str]): Nombre del bucket S3
        - raw_text (Optional[str]): Texto previamente extraído (opcional)
        
        ¿Qué dato regresa y de qué tipo?
        - Dict[str, Any]: Diccionario con datos extraídos:
          - descripcion: Descripción del documento
          - resumen: Resumen del contenido
          - sentimiento: Análisis de sentimiento (positivo/negativo/neutral)
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
        Calcula la puntuación de confianza para la clasificación.
        
        ¿Qué hace la función?
        Calcula una puntuación de confianza basada en el número de bloques de texto
        encontrados en la respuesta de Textract. Más bloques indican mayor confianza
        en que el documento fue procesado correctamente.
        
        ¿Qué parámetros recibe y de qué tipo?
        - response (Dict[str, Any]): Respuesta de AWS Textract con bloques
        - classification (str): Resultado de la clasificación ("FACTURA" o "INFORMACIÓN")
        
        ¿Qué dato regresa y de qué tipo?
        - float: Puntuación de confianza entre 0.0 y 100.0
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

