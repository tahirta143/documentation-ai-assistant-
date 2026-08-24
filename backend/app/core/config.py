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

    # ------------------------------------------------------------------
    # Database (Phase 2)
    # ------------------------------------------------------------------
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/documentation_assistant"

    # Connection pool settings — sensible defaults for a single-server dev setup
    db_pool_size: int = 5          # number of persistent connections kept open
    db_max_overflow: int = 10      # extra connections allowed above pool_size
    db_pool_recycle: int = 1800    # recycle connections after 30 min (avoids stale sockets)
    db_echo: bool = False          # set True in .env to log every SQL statement

    upload_dir: Path = BASE_DIR.parent / "data" / "uploads"
    max_upload_size_mb: int = 25

    # ------------------------------------------------------------------
    # Chunking (Phase 6)
    # ------------------------------------------------------------------
    chunk_size: int = 800
    chunk_overlap: int = 100

    # ------------------------------------------------------------------
    # Embeddings + LLM (Phase 7+)
    # ------------------------------------------------------------------
    embedding_provider: str = "openai"
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    llm_model: str = "gpt-4o-mini"
    retrieval_top_k: int = 5          # number of chunks to retrieve per query


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
