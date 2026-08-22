from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Documentation Assistant"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api"

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/documentation_assistant"

    upload_dir: Path = BASE_DIR.parent / "data" / "uploads"
    max_upload_size_mb: int = 25


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
