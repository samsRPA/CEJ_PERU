from app.domain.interfaces.IS3Manager import IS3Manager
from app.infrastucture.AWS.S3Manager import S3Manager
from dependency_injector import containers, providers
from app.domain.interfaces.IRabbitMQConsumer import IRabbitMQConsumer
from app.infrastucture.config.Settings import Settings
from app.infrastucture.rabbitmq.RabbitMQConsumer import RabbitMQConsumer

from app.domain.interfaces.IGetRecordsService import IGetRecordsService


from app.domain.interfaces.ISeleniumManager import ISeleniumManager
from app.infrastucture.browser.SeleniumManager import SeleniumManager
from app.domain.interfaces.IDataBase import IDataBase
from app.infrastucture.database.OracleDB import OracleDB
from app.infrastucture.database.repositories.DocumentsRepository import DocumentsRepository
from app.application.services.scrapper.GetRecordsService import GetRecordsService


from app.domain.interfaces.IDownloadService import IDownloadService
from app.application.services.scrapper.DownloadService import DownloadService
from app.application.services.scrapper.CEJScrapperService import CEJScrapperService
from app.application.services.scrapper.FormScrapper import FormScrapper
from app.application.services.scrapper.ScrapperService import ScrapperService
from app.domain.interfaces.ICEJScrapperService import ICEJScrapperService
from app.domain.interfaces.IFormScrapper import IFormScrapper
from app.domain.interfaces.IScrapperService import IScrapperService


class Dependencies(containers.DeclarativeContainer):
  config = providers.Configuration()
  settings: providers.Singleton[Settings] = providers.Singleton(Settings)
  wiring_config = containers.WiringConfiguration(
    modules=[
      "main",
      ]
  )
    
    # Provider de db
  data_base: providers.Singleton[IDataBase] = providers.Singleton(
    OracleDB,
    db_user=settings.provided.data_base.DB_USER,
    db_password=settings.provided.data_base.DB_PASSWORD,
    db_host=settings.provided.data_base.DB_HOST,
    db_port=settings.provided.data_base.DB_PORT,
    db_service_name=settings.provided.data_base.DB_SERVICE_NAME,
  )

  documents_repository = providers.Factory(
    DocumentsRepository,
    table_car=settings.provided.data_base_tables.DB_TABLE_NAME_CAR,
  )

  
  get_records_service : providers.Factory[IGetRecordsService] = providers.Factory(
    GetRecordsService,
  )

  S3_manager_litigando: providers.Singleton[IS3Manager] = providers.Singleton(
    S3Manager,
    awsAccessKey = settings.provided.s3.awsAccessKey,
    awsSecretKey = settings.provided.s3.awsSecretKey,
    bucketName = settings.provided.s3.bucketLitigando,
    s3Prefix = settings.provided.s3.prefixLitigando,
    )

  form_scrapper : providers.Factory[IFormScrapper] = providers.Factory(
    FormScrapper,
    get_records_service
  
    
  )


  

  download_service : providers.Factory[IDownloadService] = providers.Factory(
    DownloadService,
    S3_manager_litigando,
    documents_repository
    
  )

      # Provider del consumidor
  selenium_manager: providers.Singleton[ISeleniumManager] = providers.Singleton(
    SeleniumManager,
  )

    
  cej_scrapper_service: providers.Factory[ICEJScrapperService] = providers.Factory(
    CEJScrapperService,
    driver_selenium=selenium_manager,
    url=settings.provided.browser.URL,
    form_scrapper=form_scrapper,
    db=data_base,
    download_service=download_service 
  )


  scrapper_service: providers.Factory[IScrapperService] = providers.Factory(
    ScrapperService,
      cej_scrapper =cej_scrapper_service
    
    )

  
    # Provider del consumidor
  rabbitmq_consumer: providers.Singleton[IRabbitMQConsumer] = providers.Singleton(
    RabbitMQConsumer,
    host=settings.provided.rabbitmq.HOST,
    port=settings.provided.rabbitmq.PORT,
    pub_queue_name=settings.provided.rabbitmq.PUB_QUEUE_NAME,
    prefetch_count=settings.provided.rabbitmq.PREFETCH_COUNT,
    user=settings.provided.rabbitmq.RABBITMQ_USER,
    password=settings.provided.rabbitmq.RABBITMQ_PASS,
    scrapper_service=scrapper_service.provider
  )
