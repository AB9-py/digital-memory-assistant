from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings and environment configuration."""

    # Project Information
    PROJECT_NAME: str = "Digital Memory Assistant API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://dma:dma_local_dev_only@localhost:5432/digital_memory"
    )

    # Storage
    UPLOAD_DIR: Path = Path("./uploads")

    # Embeddings & Vector Search
    EMBEDDING_PROVIDER: str = "deterministic"  # "deterministic" or "openai"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_API_KEY: str | None = None
    EMBEDDING_DIM: int = 1536  # Default dimension for text-embedding-3-small
    DEFAULT_TOP_K: int = 5
    DEFAULT_SIMILARITY_THRESHOLD: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
