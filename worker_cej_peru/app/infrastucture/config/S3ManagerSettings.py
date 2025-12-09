from app.infrastucture.config.EnvConfig import EnvConfig
from pydantic import Field
class S3ManagerSettings(EnvConfig):
    awsAccessKey: str = Field(..., alias="S3_ACCESS_KEY")
    awsSecretKey: str = Field(..., alias="S3_SECRET")
    # Litigando
    bucketLitigando: str = Field(..., alias="S3_BUCKET_LITIGANDO")
    prefixLitigando: str = Field(..., alias="S3_PREFIX_LITIGANDO")
  