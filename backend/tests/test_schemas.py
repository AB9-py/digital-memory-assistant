import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from backend.schemas.chunk import ChunkCreate, ChunkSearchResult
from backend.schemas.memory import MemoryCreate, MemoryRead, MemoryStatus


def test_memory_create_schema() -> None:
    user_id = uuid.uuid4()
    payload = {
        "user_id": user_id,
        "original_filename": "OS_Unit_3.pdf",
        "file_type": "PDF",
        "file_size_bytes": 102400,
        "file_path": "/uploads/OS_Unit_3.pdf",
        "status": "uploaded",
        "meta_info": {"page_count": 12},
    }
    mem = MemoryCreate(**payload)
    assert mem.original_filename == "OS_Unit_3.pdf"
    assert mem.status == MemoryStatus.UPLOADED
    assert mem.meta_info["page_count"] == 12


def test_memory_read_schema() -> None:
    now = datetime.now(UTC)
    mem_id = uuid.uuid4()
    user_id = uuid.uuid4()
    mem = MemoryRead(
        id=mem_id,
        user_id=user_id,
        original_filename="notes.txt",
        file_type="TEXT",
        file_size_bytes=512,
        file_path="/uploads/notes.txt",
        status=MemoryStatus.VALIDATED,
        meta_info={},
        created_at=now,
        updated_at=now,
    )
    assert mem.id == mem_id
    assert mem.status == MemoryStatus.VALIDATED


def test_chunk_create_and_search_result_schema() -> None:
    chunk_id = uuid.uuid4()
    memory_id = uuid.uuid4()
    user_id = uuid.uuid4()

    chunk_in = ChunkCreate(
        memory_id=memory_id,
        user_id=user_id,
        chunk_index=0,
        content="Deadlock prevention involves denying one of Coffman conditions.",
        page_number=3,
        chunk_metadata={"section": "Deadlocks"},
    )
    assert chunk_in.chunk_index == 0
    assert chunk_in.page_number == 3

    search_result = ChunkSearchResult(
        chunk_id=chunk_id,
        memory_id=memory_id,
        original_filename="OS_Unit_3.pdf",
        content=chunk_in.content,
        page_number=3,
        chunk_index=0,
        similarity_score=0.92,
        chunk_metadata={"section": "Deadlocks"},
    )
    assert search_result.similarity_score == 0.92
    assert search_result.original_filename == "OS_Unit_3.pdf"


def test_chunk_create_validation_error() -> None:
    with pytest.raises(ValidationError):
        # Negative chunk_index should fail
        ChunkCreate(
            memory_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            chunk_index=-1,
            content="Invalid chunk",
        )
