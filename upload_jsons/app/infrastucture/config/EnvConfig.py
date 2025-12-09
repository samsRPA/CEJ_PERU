import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvConfig(BaseSettings):
    BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, '.env'),
        env_file_encoding='utf-8',
        extra='ignore'
    )
