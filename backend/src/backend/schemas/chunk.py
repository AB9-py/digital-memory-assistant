import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChunkBase(BaseModel):
    chunk_index: int = Field(..., ge=0)
    content: str = Field(..., min_length=1)
    page_number: int | None = Field(default=None, ge=1)
    chunk_metadata: dict[str, Any] = Field(default_factory=dict)


class ChunkCreate(ChunkBase):
    """Input payload for registering chunks from the ingestion pipeline."""

    memory_id: uuid.UUID
    user_id: uuid.UUID
    embedding: list[float] | None = None


class ChunkRead(ChunkBase):
    id: uuid.UUID
    memory_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChunkSearchResult(BaseModel):
    """Result returned from semantic vector retrieval."""

    chunk_id: uuid.UUID
    memory_id: uuid.UUID
    original_filename: str
    content: str
    page_number: int | None = None
    chunk_index: int
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    chunk_metadata: dict[str, Any] = Field(default_factory=dict)
