from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://tether:P%40ssw0rd@db:5432/tether"
    jwt_secret_key: str = "whoarewewhoarewe?moscowpolykek"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
