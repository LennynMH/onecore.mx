"""AWS Textract service for document analysis."""

import logging
import io
from typing import Optional, Dict, Any
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
            if s3_key and s3_bucket:
                response = self._analyze_from_s3(s3_bucket, s3_key)
            else:
                # Analyze from bytes (for smaller files)
                response = self._analyze_from_bytes(file_content)
            
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
    
    def _analyze_from_s3(self, bucket: str, key: str) -> Dict[str, Any]:
        """Analyze document from S3."""
        response = self.textract_client.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            }
        )
        return response
    
    def _analyze_from_bytes(self, file_content: bytes) -> Dict[str, Any]:
        """Analyze document from bytes."""
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

