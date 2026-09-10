from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NFT_", env_file=".env", extra="ignore")
    environment: str = "development"
    database_url: SecretStr
    redis_url: SecretStr
