"""Document upload use cases."""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import UploadFile

from app.domain.entities.document import Document, Event
from app.domain.repositories.document_repository import DocumentRepository
from app.infrastructure.s3.s3_service import S3Service
from app.infrastructure.ai.textract_service import TextractService
from app.infrastructure.ai.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class DocumentUploadUseCases:
    """Document upload use cases."""
    
    def __init__(
        self,
        s3_service: S3Service,
        document_repository: DocumentRepository,
        textract_service: Optional[TextractService] = None,
        openai_service: Optional[OpenAIService] = None
    ):
        """Initialize use cases with services."""
        self.s3_service = s3_service
        self.document_repository = document_repository
        self.textract_service = textract_service or TextractService()
        self.openai_service = openai_service
    
    @staticmethod
    def _generate_unique_filename(original_filename: str) -> str:
        """
        Generate unique filename with timestamp to avoid duplicates.
        
        Format: nombre_archivo_ddmmyyyyhhmmss.extension
        Example: invoice.pdf -> invoice_18122025201153.pdf
        
        Args:
            original_filename: Original filename from upload
            
        Returns:
            Filename with timestamp suffix
        """
        # Get file name and extension
        name, ext = os.path.splitext(original_filename)
        
        # Generate timestamp: ddmmyyyyhhmmss
        timestamp = datetime.utcnow().strftime('%d%m%Y%H%M%S')
        
        # Combine: nombre_timestamp.extension
        unique_filename = f"{name}_{timestamp}{ext}"
        
        return unique_filename
    
    @staticmethod
    def _get_file_type(filename: str) -> str:
        """
        Get file type from filename.
        
        Args:
            filename: Filename with extension
            
        Returns:
            File type (PDF, JPG, PNG)
        """
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.pdf':
            return 'PDF'
        elif ext in ['.jpg', '.jpeg']:
            return 'JPG'
        elif ext == '.png':
            return 'PNG'
        else:
            return ext.upper().replace('.', '')
    
    async def upload_document(
        self,
        file: UploadFile,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Upload document to S3 and database.
        
        Args:
            file: Document file to upload (PDF, JPG, PNG)
            user_id: ID of user uploading the document
            
        Returns:
            Dictionary with upload result
        """
        try:
            # Validate file type
            file_type = self._get_file_type(file.filename)
            if file_type not in ['PDF', 'JPG', 'PNG']:
                raise ValueError(f"Invalid file type: {file_type}. Only PDF, JPG, PNG are allowed.")
            
            # Generate unique filename with timestamp
            unique_filename = self._generate_unique_filename(file.filename)
            
            # Read file content to get size (before S3 upload)
            file_content = await file.read()
            file_size = len(file_content)
            # Reset file pointer for S3 upload
            await file.seek(0)
            
            # Try to upload to S3
            s3_key = None
            s3_bucket = None
            try:
                # Use unique filename in S3 path
                s3_key_path = f"documents/{datetime.utcnow().strftime('%Y/%m/%d')}/{unique_filename}"
                s3_key = await self.s3_service.upload_file(file, s3_key_path)
                if s3_key:
                    from app.core.config import settings
                    s3_bucket = settings.aws_s3_bucket_name
                    logger.info(f"Document successfully uploaded to S3: {s3_key}")
                else:
                    logger.warning("S3 upload skipped (not configured). Document will be saved to database only.")
            except Exception as e:
                logger.warning(f"S3 upload failed: {str(e)}. Continuing with database save only.")
                s3_key = None
                s3_bucket = None
            
            # Classify document using AWS Textract (FASE 2)
            classification = None
            processing_time_ms = None
            analysis_result = None
            
            try:
                from app.core.config import settings
                if settings.aws_textract_enabled:
                    logger.info("Starting document classification with AWS Textract...")
                    analysis_result = await self.textract_service.analyze_document(
                        file=file,
                        s3_key=s3_key,
                        s3_bucket=s3_bucket
                    )
                    classification = analysis_result.get("classification", "INFORMACIÓN")
                    processing_time_ms = analysis_result.get("processing_time_ms", 0)
                    
                    if analysis_result.get("error"):
                        logger.warning(f"Textract analysis completed with errors: {analysis_result.get('error')}")
                    else:
                        logger.info(f"Document classified as: {classification} (confidence: {analysis_result.get('confidence', 0):.2f}%)")
                else:
                    logger.info("AWS Textract is disabled. Skipping classification.")
            except Exception as e:
                logger.warning(f"Error during document classification: {str(e)}. Continuing with upload.")
                classification = "INFORMACIÓN"  # Default classification
            
            # Create document entity
            processed_at = datetime.utcnow() if classification else None
            document = Document(
                filename=unique_filename,
                original_filename=file.filename,
                file_type=file_type,
                s3_key=s3_key,
                s3_bucket=s3_bucket,
                classification=classification,  # Set from Textract analysis
                uploaded_by=user_id,
                file_size=file_size,
                processed_at=processed_at  # Set when classification is done
            )
            
            # Save document to database
            document = await self.document_repository.save_document(document)
            
            # Register DOCUMENT_UPLOAD event
            try:
                event = Event(
                    event_type="DOCUMENT_UPLOAD",
                    description=f"Document uploaded: {file.filename}",
                    document_id=document.id,
                    user_id=user_id
                )
                await self.document_repository.save_event(event)
            except Exception as e:
                logger.warning(f"Failed to register DOCUMENT_UPLOAD event: {str(e)}")
            
            # Register AI_PROCESSING event if classification was performed
            if classification and analysis_result and not analysis_result.get("error"):
                try:
                    ai_event = Event(
                        event_type="AI_PROCESSING",
                        description=f"Document classified as {classification} using AWS Textract (confidence: {analysis_result.get('confidence', 0):.2f}%)",
                        document_id=document.id,
                        user_id=user_id
                    )
                    await self.document_repository.save_event(ai_event)
                except Exception as e:
                    logger.warning(f"Failed to register AI_PROCESSING event: {str(e)}")
            
            # FASE 3: Extract structured data based on classification
            extracted_data = None
            try:
                from app.core.config import settings
                raw_text = analysis_result.get("raw_text") if analysis_result else None
                
                if classification == "FACTURA":
                    logger.info("Extracting invoice data...")
                    # Reset file pointer for extraction
                    await file.seek(0)
                    invoice_data = await self.textract_service.extract_invoice_data(
                        file=file,
                        s3_key=s3_key,
                        s3_bucket=s3_bucket,
                        raw_text=raw_text
                    )
                    
                    if invoice_data:
                        # Save extracted data to database
                        await self.document_repository.save_extracted_data(
                            document_id=document.id,
                            data_type="INVOICE",
                            extracted_data=invoice_data
                        )
                        extracted_data = invoice_data
                        logger.info(f"Invoice data extracted and saved: {len(invoice_data)} fields")
                
                elif classification == "INFORMACIÓN":
                    logger.info("Extracting information data...")
                    # Reset file pointer for extraction
                    await file.seek(0)
                    information_data = await self.textract_service.extract_information_data(
                        file=file,
                        s3_key=s3_key,
                        s3_bucket=s3_bucket,
                        raw_text=raw_text
                    )
                    
                    # Use OpenAI for sentiment analysis if available
                    if self.openai_service and information_data.get("resumen"):
                        try:
                            from app.core.config import settings
                            if settings.openai_enabled:
                                logger.info("Analyzing sentiment with OpenAI...")
                                sentiment = await self.openai_service.analyze_sentiment(
                                    information_data.get("resumen", "")
                                )
                                information_data["sentimiento"] = sentiment
                                
                                # Generate better summary if OpenAI is available
                                if raw_text:
                                    summary = await self.openai_service.generate_summary(raw_text)
                                    if summary:
                                        information_data["resumen"] = summary
                        except Exception as e:
                            logger.warning(f"Error using OpenAI for sentiment analysis: {str(e)}")
                    
                    if information_data:
                        # Save extracted data to database
                        await self.document_repository.save_extracted_data(
                            document_id=document.id,
                            data_type="INFORMATION",
                            extracted_data=information_data
                        )
                        extracted_data = information_data
                        logger.info(f"Information data extracted and saved: {len(information_data)} fields")
                
            except Exception as e:
                logger.warning(f"Error during data extraction: {str(e)}. Continuing without extracted data.")
                # Don't fail the upload if extraction fails
            
            return {
                "success": True,
                "message": "Document uploaded successfully to S3 and database",
                "document_id": document.id,
                "filename": document.filename,
                "original_filename": document.original_filename,
                "s3_key": document.s3_key,
                "s3_bucket": document.s3_bucket,
                "classification": document.classification,
                "extracted_data": extracted_data,  # FASE 3: Datos extraídos
                "processing_time_ms": processing_time_ms
            }
            
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            raise Exception(f"Failed to upload document: {str(e)}")

