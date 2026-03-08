"""Environment variable configuration for the data service."""

from pathlib import Path

from pydantic_settings import BaseSettings

_DATA_DIR = Path(__file__).resolve().parents[3] / "data"


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{(_DATA_DIR / 'data.db').as_posix()}"
    duck_db_path: str = (_DATA_DIR / "data.duckdb").as_posix()
    log_level: str = "INFO"
    upload_dir: str = "uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100 MB

    model_config = {"env_file": ".env"}


settings = Settings()
