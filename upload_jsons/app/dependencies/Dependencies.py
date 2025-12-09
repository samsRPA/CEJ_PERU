from dependency_injector import containers, providers
from app.infrastucture.config.Settings import Settings
from app.domain.interfaces.IDataBase import IDataBase
from app.infrastucture.database.OracleDB import OracleDB
from app.domain.interfaces.IBulkUploadService import IBulkUploadService
from app.application.services.BulkUploadService import BulkUploadService
from app.infrastucture.database.repositories.CargaMasivaCJRepository import CargaMasivaCJRepository

class Dependencies(containers.DeclarativeContainer):
    config = providers.Configuration()
    settings: providers.Singleton[Settings] = providers.Singleton(Settings)

# Provider de db
    data_base: providers.Singleton[IDataBase] = providers.Singleton(
        OracleDB,
        db_user=settings.provided.data_base.DB_USER,
        db_password=settings.provided.data_base.DB_PASSWORD,
        db_host=settings.provided.data_base.DB_HOST,
        db_port=settings.provided.data_base.DB_PORT,
        db_service_name=settings.provided.data_base.DB_SERVICE_NAME,
    )

    carga_masiva_cj_repository = providers.Factory(
        CargaMasivaCJRepository,
    )


    bulk_upload_service: providers.Factory[IBulkUploadService] = providers.Factory(
        BulkUploadService,
        db=data_base,
        repository=carga_masiva_cj_repository
    )
        



 
