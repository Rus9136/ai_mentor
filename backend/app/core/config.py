"""
Application configuration.
"""
from typing import Optional
from pydantic_settings import BaseSettings


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
        """Build async database URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # LangChain / LLM
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4"
    EMBEDDING_MODEL: str = "text-embedding-3-small"

    # RAG
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 5

    # Adaptive Learning
    MASTERY_THRESHOLD: float = 0.7
    DAYS_TO_TRACK: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
