"""Application configuration loaded from environment variables.

Single source of truth for runtime settings. Reads .env on import.
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_upload_dir() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    upload_path = repo_root / "data" / "uploads"
    upload_path.mkdir(parents=True, exist_ok=True)
    return str(upload_path)


def _default_database_url() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    db_path = repo_root / "data" / "tdr_review.db"
    return f"sqlite:///{db_path}"


class Settings(BaseSettings):
    """Runtime settings for the TDR Review web app."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM provider for the deployed web demo
    # Acepta GOOGLE_API_KEY o GEMINI_API_KEY (nombre usado por Google AI Studio)
    google_api_key: str = Field(
        "", validation_alias=AliasChoices("GOOGLE_API_KEY", "GEMINI_API_KEY")
    )
    rag_use_google_llm: bool = True
    rag_gemini_model: str = "gemini-2.5-flash"
    rag_qwen_4bit: bool = False

    # Embeddings
    rag_embeddings_backend: str = "cpu-e5"

    # Vector store V2 (Qdrant Cloud). Acepta QDRANT_URL o QDRANT_ENDPOINT.
    qdrant_url: str = Field(
        "", validation_alias=AliasChoices("QDRANT_URL", "QDRANT_ENDPOINT")
    )
    qdrant_api_key: str = ""

    # Persistence
    database_url: str = os.environ.get("DATABASE_URL") or _default_database_url()
    upload_dir: str = os.environ.get("UPLOAD_DIR") or _default_upload_dir()

    # Limits
    max_upload_bytes: int = 20 * 1024 * 1024  # 20MB
    max_text_chars: int = 50_000
    min_text_chars: int = 200

    # Analysis
    grounding_threshold: float = 0.25
    use_reranker_in_web: bool = False


_settings: Settings | None = None


def get_settings() -> Settings:
    """Lazy singleton for settings to keep tests predictable."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings_cache() -> None:
    """Reset the cached settings (useful for tests)."""
    global _settings
    _settings = None