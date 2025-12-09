from pydantic_settings import BaseSettings


from app.infrastucture.config.RabbitMQSettings import RabbitMQSettings

from app.infrastucture.config.DataBaseSettings import DataBaseSettings
from app.infrastucture.config.DataBaseTablesSettings import DataBaseTablesSettings
from app.infrastucture.config.S3ManagerSettings import S3ManagerSettings
from app.infrastucture.config.BrowserConfig import BrowserConfig

class Settings(BaseSettings):
    browser:BrowserConfig = BrowserConfig()
    rabbitmq : RabbitMQSettings = RabbitMQSettings()
    data_base: DataBaseSettings = DataBaseSettings()
    data_base_tables: DataBaseTablesSettings = DataBaseTablesSettings()
    s3 : S3ManagerSettings = S3ManagerSettings()
    
def load_config() -> Settings:
    return Settings()
