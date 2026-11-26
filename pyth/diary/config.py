from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    database_url: str = "postgresql+psycopg://tether:P%40ssw0rd@db:5432/tether"
    jwt_secret_key: str = "whoarewewhoarewe?moscowpolykek"
    jwt_algorithm: str = "HS256"
    admin_api_key: str = "tester"
    environment: str = "development"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def getcfg() -> Config:
    return Config()
