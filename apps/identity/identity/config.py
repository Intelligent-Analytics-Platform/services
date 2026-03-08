"""Application settings loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_DATA_DIR = Path(__file__).resolve().parents[3] / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = f"sqlite:///{(_DATA_DIR / 'identity.db').as_posix()}"
    log_level: str = "INFO"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8001

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
