import uuid

from backend.models import Base, Chunk, Memory, User


def test_models_metadata_registered() -> None:
    """Verify all ORM models are registered with Base metadata."""
    table_names = Base.metadata.tables.keys()
    assert "users" in table_names
    assert "memories" in table_names
    assert "chunks" in table_names


def test_model_instantiation() -> None:
    user_id = uuid.uuid4()
    memory_id = uuid.uuid4()
    chunk_id = uuid.uuid4()

    user = User(id=user_id, email="test@example.com")
    memory = Memory(
        id=memory_id,
        user_id=user_id,
        original_filename="notes.pdf",
        file_type="PDF",
        file_path="/uploads/notes.pdf",
        file_size_bytes=2048,
        status="uploaded",
        meta_info={"author": "Student"},
    )
    chunk = Chunk(
        id=chunk_id,
        memory_id=memory_id,
        user_id=user_id,
        chunk_index=0,
        content="Testing chunk content",
        page_number=1,
        embedding=[0.1] * 1536,
        chunk_metadata={"tag": "notes"},
    )

    assert user.email == "test@example.com"
    assert memory.original_filename == "notes.pdf"
    assert chunk.content == "Testing chunk content"
    assert len(chunk.embedding) == 1536
