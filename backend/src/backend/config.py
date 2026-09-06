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
    EMBEDDING_DIM: int = 1536  # Default dimension for text-embedding-3-small
    DEFAULT_TOP_K: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
