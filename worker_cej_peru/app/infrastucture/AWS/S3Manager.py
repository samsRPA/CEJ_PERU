import boto3
from pathlib import Path
from botocore.exceptions import BotoCoreError, ClientError
import logging

import os

from app.domain.interfaces.IS3Manager import IS3Manager
 
class S3Manager(IS3Manager):

    logger = logging.getLogger(__name__)
    
    def __init__(self, awsAccessKey: str, awsSecretKey: str, bucketName: str, s3Prefix: str):
        self.bucketName = bucketName
        self.prefix = s3Prefix.rstrip("/") 
        self.s3 = boto3.client(
            's3',
            aws_access_key_id = awsAccessKey,
            aws_secret_access_key = awsSecretKey
        )


    def uploadFile(self, file_path: str) -> bool:
        """
        Sube un archivo a S3.
        Retorna True si se subió exitosamente, False en caso de error.
        """
        s3_key = f"{self.prefix}/{os.path.basename(file_path)}" if self.prefix else os.path.basename(file_path)

        try:
            self.s3.upload_file(file_path, self.bucketName, s3_key)
            self.logger.info(f"📤 Subido a S3: s3://{self.bucketName}/{s3_key}")
            return True
        except (BotoCoreError, ClientError, Exception) as e:
            self.logger.error(f"❌ Error subiendo a S3 {file_path}: {e}")
            return False