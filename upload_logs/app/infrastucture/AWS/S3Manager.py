import os
import logging
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.domain.interfaces.IS3Manager import IS3Manager

class S3Manager(IS3Manager):
    
    def __init__(self, awsAccessKey: str, awsSecretKey: str, bucketName: str, s3Prefix: str):
        self.bucketName = bucketName
        self.prefix = s3Prefix.rstrip("/") 
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=awsAccessKey,
            aws_secret_access_key=awsSecretKey
        )
        self.logger = logging.getLogger(__name__)

    def uploadFile(self, file_path: str, s3_key: str) -> bool:
        """
        Sube un archivo a S3 usando la ruta completa (s3_key) proporcionada.
        """
        try:
            self.s3.upload_file(file_path, self.bucketName, s3_key)
            self.logger.info(f"📤 Subido a S3: s3://{self.bucketName}/{s3_key}")
            return True
        except (BotoCoreError, ClientError, Exception) as e:
            self.logger.error(f"❌ Error subiendo a S3 {file_path}: {e}")
            return False
