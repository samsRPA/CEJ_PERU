from pydantic_settings import BaseSettings

from app.infrastucture.config.S3ManagerSettings import S3ManagerSettings




class Settings(BaseSettings):
    s3 : S3ManagerSettings = S3ManagerSettings()
    
   

def load_config() -> Settings:
    return Settings()
