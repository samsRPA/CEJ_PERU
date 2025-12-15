from dependency_injector import containers, providers
from app.infrastucture.config.Settings import Settings

from app.domain.interfaces.IBulkUploadService import IBulkUploadService
from app.application.services.BulkUploadService import BulkUploadService
from app.domain.interfaces.IS3Manager import IS3Manager
from app.infrastucture.AWS.S3Manager import S3Manager


class Dependencies(containers.DeclarativeContainer):
    config = providers.Configuration()
    settings: providers.Singleton[Settings] = providers.Singleton(Settings)

       #Provider S3 - Litigando
    S3_manager_litigando: providers.Singleton[IS3Manager] = providers.Singleton(
        S3Manager,
        awsAccessKey = settings.provided.s3.awsAccessKey,
        awsSecretKey = settings.provided.s3.awsSecretKey,
        bucketName = settings.provided.s3.bucketLitigando,
        s3Prefix = settings.provided.s3.prefixLitigando,
    )


    bulk_upload_service: providers.Factory[IBulkUploadService] = providers.Factory(
        BulkUploadService,
        S3_manager_litigando
    )
        



 
