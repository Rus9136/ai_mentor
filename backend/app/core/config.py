"""
Application configuration.
"""
from typing import Optional
from pathlib import Path
from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# Получаем абсолютный путь к .env файлу
# Этот файл: backend/app/core/config.py
# .env файл: backend/.env
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/app/
ENV_PATH = BASE_DIR.parent / ".env"  # backend/.env

# Load .env file with priority (override=True)
# This will override any environment variables with values from .env
if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)
else:
    import warnings
    warnings.warn(f".env file not found at: {ENV_PATH}")


class Settings(BaseSettings):
    """Application settings."""

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "AI Mentor"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Database
    POSTGRES_USER: str = "ai_mentor_user"
    POSTGRES_PASSWORD: str = "ai_mentor_pass"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "ai_mentor_db"

    @property
    def database_url(self) -> str:
        """Build database URL."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def async_database_url(self) -> str:
        """
        Build async database URL.

        Используем asyncpg - он работает, но требует selectinload вместо joinedload для relationships.
        ssl=disable нужен для внутренней Docker-сети (postgres без SSL).
        """
        from urllib.parse import quote_plus
        # URL-encode password для спецсимволов (@, !, etc.)
        password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}?ssl=disable"
        )

    # JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_ID_MOBILE: Optional[str] = None  # For mobile app later

    # CORS
    # Поддерживает как list[str] так и CSV строку "domain1,domain2,domain3"
    BACKEND_CORS_ORIGINS: list[str] | str = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",  # Vite dev server (default port)
        "http://localhost:5174",  # Vite dev server (alternative port)
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """
        Парсит BACKEND_CORS_ORIGINS из CSV строки или возвращает list как есть.

        Примеры:
        - "https://ai-mentor.kz,https://admin.ai-mentor.kz" → ["https://ai-mentor.kz", "https://admin.ai-mentor.kz"]
        - ["https://ai-mentor.kz"] → ["https://ai-mentor.kz"]
        """
        if isinstance(v, str):
            # Парсим CSV: разделяем по запятой и удаляем пробелы
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # LangChain / LLM
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Jina AI Embeddings (free tier: 1M tokens/month)
    JINA_API_KEY: Optional[str] = None
    JINA_EMBEDDING_MODEL: str = "jina-embeddings-v3"
    EMBEDDING_PROVIDER: str = "jina"  # openai | jina
    EMBEDDING_DIMENSIONS: int = 1024  # 1024 for Jina, can be 1536 for OpenAI

    # OpenRouter / Cerebras (cost-effective LLM provider)
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_PROVIDER: str = "openrouter"  # openai | openrouter
    CEREBRAS_MODEL: str = "cerebras/llama-3.3-70b"  # ~$0.50/1M tokens

    # RAG
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 5
    MIN_SIMILARITY: float = 0.5  # Minimum cosine similarity for vector search

    # Adaptive Learning
    MASTERY_THRESHOLD: float = 0.7
    DAYS_TO_TRACK: int = 30

    # File Uploads
    UPLOAD_DIR: str = "uploads"
    MAX_IMAGE_SIZE_MB: int = 5
    MAX_PDF_SIZE_MB: int = 50
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/webp", "image/gif"]

    model_config = ConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
