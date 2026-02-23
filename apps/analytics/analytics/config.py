"""Environment variable configuration for the analytics service."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Path to the DuckDB file written by the data service (opened read-only here)
    duck_db_path: str = "../data/data.duckdb"

    # Downstream service URLs
    vessel_service_url: str = "http://localhost:8002"
    meta_service_url: str = "http://localhost:8000"

    # Directory containing XGBoost pkl model files for speed/trim optimisation
    models_dir: str = "./models"

    log_level: str = "INFO"

    model_config = {"env_file": ".env"}


settings = Settings()
