"""Environment variable configuration for the data service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data.db"
    duck_db_path: str = "./data.duckdb"
    log_level: str = "INFO"
    upload_dir: str = "uploads"
    max_file_size: int = 100 * 1024 * 1024  # 100 MB

    model_config = {"env_file": ".env"}


settings = Settings()
