"""Environment variable configuration for the analytics service."""

from pathlib import Path

from pydantic_settings import BaseSettings

_DATA_DIR = Path(__file__).resolve().parents[3] / "data"


class Settings(BaseSettings):
    # Path to the DuckDB file written by the data service (opened read-only here)
    duck_db_path: str = (_DATA_DIR / "data.duckdb").as_posix()

    # Downstream service URLs
    vessel_service_url: str = "http://localhost:8002"
    meta_service_url: str = "http://localhost:8000"

    # Directory containing XGBoost pkl model files for speed/trim optimisation
    models_dir: str = "./models"

    log_level: str = "INFO"

    model_config = {"env_file": ".env"}


settings = Settings()
