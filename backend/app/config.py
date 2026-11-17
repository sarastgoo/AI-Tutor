"""Application settings loaded from environment variables."""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All app settings. Loaded from .env or environment."""

    model_config = SettingsConfigDict(
        env_file=r"C:\Projects\ai-english-tutor\.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    ENVIRONMENT: Literal["dev", "test", "prod"] = "dev"
    LOG_LEVEL: str = "INFO"
    APP_VERSION: str = "0.1.0"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    # --- Database ---
    DATABASE_URL: str
    DATABASE_URL_SYNC: str
    POSTGRES_USER: str = "tutor"
    POSTGRES_PASSWORD: str = "devpassword"
    POSTGRES_DB: str = "tutor_dev"
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5433

    # --- Ollama ---
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen3:4b"

    # --- Storage ---
    STORAGE_ROOT: Path = Path(r"C:\Projects\ai-english-tutor\storage")
    IMPORT_ROOT: Path = Path(r"C:\Projects\ai-english-tutor\scripts\fixtures")

    # --- Embeddings ---
    EMBEDDING_MODEL: str = "intfloat/multilingual-e5-small"
    EMBEDDING_DIM: int = 384

    # --- OCR ---
    OCR_LANG: str = "en"
    OCR_USE_GPU: bool = False

    # --- STT ---
    WHISPER_MODEL: str = "small"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    # --- TTS ---
    PIPER_VOICE_PATH: Path = Path(r"C:\Projects\ai-english-tutor\scripts\voices\en_US-lessac-medium.onnx")
    PIPER_VOICE_CONFIG: Path = Path(r"C:\Projects\ai-english-tutor\scripts\voices\en_US-lessac-medium.onnx.json")

    # --- Security ---
    ALLOW_NON_LOOPBACK: bool = False

    @field_validator("STORAGE_ROOT", "IMPORT_ROOT", "PIPER_VOICE_PATH", "PIPER_VOICE_CONFIG", mode="before")
    @classmethod
    def _expand_path(cls, v: str | Path) -> Path:
        return Path(v).expanduser().resolve()

    @field_validator("APP_HOST")
    @classmethod
    def _check_loopback(cls, v: str) -> str:
        # In dev, refuse non-loopback binding unless explicitly allowed
        if not v.startswith("127.") and v != "localhost":
            import os

            if os.getenv("ALLOW_NON_LOOPBACK", "false").lower() != "true":
                raise ValueError(
                    f"APP_HOST={v} is not loopback. Set ALLOW_NON_LOOPBACK=true to override."
                )
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Singleton for convenience
settings = get_settings()