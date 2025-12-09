from pydantic import Field
from app.infrastucture.config.EnvConfig import EnvConfig


class RabbitMQSettings(EnvConfig):
    HOST: str = Field(..., alias="RABBITMQ_HOST")
    PORT: int = Field(..., alias="RABBITMQ_PORT")
    PUB_QUEUE_NAME: str = Field(..., alias="PUB_QUEUE_NAME")
    PREFETCH_COUNT: int = Field(..., alias="PREFETCH_COUNT")
    RABBITMQ_USER: str = Field(..., alias="RABBITMQ_USER")
    RABBITMQ_PASS: str = Field(..., alias="RABBITMQ_PASS")
