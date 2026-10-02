from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres@localhost:5432/aitechnician"
    secret_key: str = "change-me"
    session_https_only: bool = False
    session_max_age_seconds: int = 8 * 60 * 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
