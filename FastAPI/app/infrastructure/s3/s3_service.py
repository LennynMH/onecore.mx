"""AWS S3 service for file storage."""

import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for AWS S3 operations."""
    
    def __init__(self):
        """Initialize S3 client."""
        if not settings.aws_access_key_id or not settings.aws_secret_access_key:
            logger.warning("AWS credentials not configured. S3 uploads will fail.")
            self.s3_client = None
            self.bucket_name = None
        else:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region
            )
            self.bucket_name = settings.aws_s3_bucket_name
    
    async def upload_file(
        self,
        file: UploadFile,
        s3_key: str
    ) -> Optional[str]:
        """
        Upload file to S3.
        
        Args:
            file: FastAPI UploadFile object
            s3_key: S3 object key (path)
            
        Returns:
            S3 key if successful, None if S3 is not configured or fails
        """
        if not self.s3_client or not self.bucket_name:
            logger.warning("AWS S3 credentials not configured. Skipping S3 upload. File will be saved to database only.")
            return None
        
        try:
            # Read file content
            file_content = await file.read()
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type or 'text/csv'
            )
            
            logger.info(f"File uploaded to S3: {s3_key}")
            return s3_key
            
        except ClientError as e:
            logger.warning(f"Error uploading file to S3: {str(e)}. Continuing with database save only.")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error uploading file to S3: {str(e)}. Continuing with database save only.")
            return None
    
    def get_file_url(self, s3_key: str, expiration: int = 3600) -> str:
        """
        Generate presigned URL for file access.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds
            
        Returns:
            Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise Exception(f"Failed to generate file URL: {str(e)}")

