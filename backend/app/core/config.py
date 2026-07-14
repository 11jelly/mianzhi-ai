from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str | None = None
    jwt_secret_key: str = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"
    jwt_access_token_expire_minutes: int = 120
    llm_api_key: str | None = None
    llm_model: str = "qwen-plus"
    llm_base_url: str | None = None
    max_follow_ups_per_session: int = 2
    max_follow_ups_per_primary: int = 1
    follow_up_min_score: int = 1
    follow_up_score_threshold: int = 60
    asr_api_key: str | None = None
    asr_model: str = "qwen3-asr-flash"
    asr_max_duration_seconds: int = 300
    asr_max_file_size_mb: int = 10
    embedding_api_key: str | None = None
    embedding_model: str = "text-embedding-v4"
    embedding_dimension: int = 1024
    rag_top_k: int = 4
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 80
    rag_max_document_size_mb: int = 5

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
