import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.models.memory import Memory
from backend.schemas.chunk import ChunkSearchResult
from backend.schemas.memory import MemoryStatus

client = TestClient(app)


def test_api_search_endpoint() -> None:
    user_id = uuid.uuid4()
    memory_id = uuid.uuid4()
    chunk_id = uuid.uuid4()

    mock_result = [
        ChunkSearchResult(
            chunk_id=chunk_id,
            memory_id=memory_id,
            original_filename="OS_Unit_3.pdf",
            content="Banker's algorithm is a deadlock avoidance algorithm.",
            page_number=5,
            chunk_index=2,
            similarity_score=0.94,
            chunk_metadata={"section": "Deadlocks"},
        )
    ]

    with patch(
        "backend.api.memories.retrieval_service.search_memories",
        new_callable=AsyncMock,
    ) as mock_search:
        mock_search.return_value = mock_result

        response = client.post(
            "/api/v1/memories/search",
            json={
                "query": "Banker algorithm deadlock avoidance",
                "user_id": str(user_id),
                "top_k": 3,
                "min_similarity": 0.5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Banker algorithm deadlock avoidance"
        assert data["total_results"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["original_filename"] == "OS_Unit_3.pdf"
        assert data["results"][0]["similarity_score"] == 0.94


def test_api_ingest_endpoint() -> None:
    user_id = uuid.uuid4()
    memory_id = uuid.uuid4()
    now = datetime.now(UTC)

    mock_memory = Memory(
        id=memory_id,
        user_id=user_id,
        original_filename="notes.txt",
        file_type="TEXT",
        file_path="/uploads/notes.txt",
        file_size_bytes=128,
        status=MemoryStatus.PROCESSED.value,
        meta_info={},
        created_at=now,
        updated_at=now,
    )

    with patch(
        "backend.api.memories.memory_service.ingest_memory_with_chunks",
        new_callable=AsyncMock,
    ) as mock_ingest:
        mock_ingest.return_value = mock_memory

        response = client.post(
            "/api/v1/memories/ingest",
            json={
                "user_id": str(user_id),
                "original_filename": "notes.txt",
                "file_type": "TEXT",
                "file_path": "/uploads/notes.txt",
                "file_size_bytes": 128,
                "chunks": [
                    {
                        "chunk_index": 0,
                        "content": "First line of notes.",
                        "page_number": 1,
                    }
                ],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(memory_id)
        assert data["original_filename"] == "notes.txt"
        assert data["status"] == "processed"


def test_api_list_memories_endpoint() -> None:
    user_id = uuid.uuid4()
    memory_id = uuid.uuid4()
    now = datetime.now(UTC)

    mock_memory = Memory(
        id=memory_id,
        user_id=user_id,
        original_filename="lecture.pdf",
        file_type="PDF",
        file_path="/uploads/lecture.pdf",
        file_size_bytes=2048,
        status=MemoryStatus.PROCESSED.value,
        meta_info={},
        created_at=now,
        updated_at=now,
    )

    with patch(
        "backend.api.memories.memory_service.list_memories",
        new_callable=AsyncMock,
    ) as mock_list:
        mock_list.return_value = (1, [mock_memory])

        response = client.get(f"/api/v1/memories?user_id={user_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["original_filename"] == "lecture.pdf"


def test_api_delete_memory_endpoint() -> None:
    user_id = uuid.uuid4()
    memory_id = uuid.uuid4()

    with patch(
        "backend.api.memories.memory_service.delete_memory",
        new_callable=AsyncMock,
    ) as mock_delete:
        mock_delete.return_value = True

        response = client.delete(f"/api/v1/memories/{memory_id}?user_id={user_id}")

        assert response.status_code == 200
        assert response.json() == {"deleted": True}


def test_api_delete_memory_not_found() -> None:
    user_id = uuid.uuid4()
    memory_id = uuid.uuid4()

    with patch(
        "backend.api.memories.memory_service.delete_memory",
        new_callable=AsyncMock,
    ) as mock_delete:
        mock_delete.return_value = False

        response = client.delete(f"/api/v1/memories/{memory_id}?user_id={user_id}")

        assert response.status_code == 404
