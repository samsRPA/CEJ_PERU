from pydantic_settings import BaseSettings



from app.infrastucture.config.DataBaseSettings import DataBaseSettings

class Settings(BaseSettings):
 
    data_base: DataBaseSettings = DataBaseSettings()
   

def load_config() -> Settings:
    return Settings()
