import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.chunk import ChunkBase


class MemoryStatus(str, Enum):
    UPLOADED = "uploaded"
    VALIDATED = "validated"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    REJECTED = "rejected"


class MemoryBase(BaseModel):
    original_filename: str = Field(..., max_length=255)
    file_type: str = Field(..., max_length=50)
    file_size_bytes: int = Field(..., ge=0)
    meta_info: dict[str, Any] = Field(default_factory=dict)


class MemoryCreate(MemoryBase):
    user_id: uuid.UUID
    file_path: str
    status: MemoryStatus = MemoryStatus.UPLOADED


class MemoryIngestRequest(MemoryBase):
    """Payload sent by the ingestion worker containing document metadata and extracted text chunks."""

    user_id: uuid.UUID
    file_path: str
    chunks: list[ChunkBase] = Field(default_factory=list)


class MemoryUpdateStatus(BaseModel):
    status: MemoryStatus
    meta_info: dict[str, Any] | None = None


class MemoryRead(MemoryBase):
    id: uuid.UUID
    user_id: uuid.UUID
    file_path: str
    status: MemoryStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryListResponse(BaseModel):
    total: int
    items: list[MemoryRead]
