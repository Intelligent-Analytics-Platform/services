"""Configuration settings for the vessel service."""

from pathlib import Path

from pydantic_settings import BaseSettings

_DATA_DIR = Path(__file__).resolve().parents[3] / "data"


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{(_DATA_DIR / 'vessel.db').as_posix()}"
    log_level: str = "INFO"
    analytics_service_url: str = "http://localhost:9005"
    analytics_timeout_seconds: int = 3

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
