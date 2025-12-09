from pydantic import Field
from app.infrastucture.config.EnvConfig import EnvConfig


class BrowserConfig(EnvConfig):
    URL: str = Field(..., alias="URL")
