import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db
from backend.schemas.memory import (
    MemoryIngestRequest,
    MemoryListResponse,
    MemoryRead,
)
from backend.schemas.search import SearchRequest, SearchResponse
from backend.services.extraction import extract_chunks
from backend.services.memory_service import memory_service
from backend.services.retrieval_service import retrieval_service

router = APIRouter(prefix="/memories", tags=["memories"])

_ALLOWED_EXTENSIONS: dict[str, str] = {
    ".pdf": "PDF",
    ".txt": "TEXT",
    ".docx": "DOCX",
    ".png": "IMAGE",
    ".jpg": "IMAGE",
    ".jpeg": "IMAGE",
}
_MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


@router.post(
    "/upload",
    response_model=MemoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file — validate, extract, chunk, embed, and store in one request",
)
async def upload_memory(
    user_id: Annotated[uuid.UUID, Query(description="Owner user ID")],
    file: UploadFile,
    db: DatabaseSession,
) -> MemoryRead:
    """
    Accepts multipart/form-data. Validates extension + size, extracts text chunks
    in-process (PDF/TXT/DOCX/image-OCR), embeds them, and persists to pgvector.
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{suffix}'. Allowed: {sorted(_ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Uploaded file is empty.")
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 20 MB limit.")

    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    dest_path = settings.UPLOAD_DIR / safe_name
    dest_path.write_bytes(content)

    file_type = _ALLOWED_EXTENSIONS[suffix]
    try:
        chunks = extract_chunks(dest_path, file_type)
    except Exception as exc:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Text extraction failed: {exc}",
        ) from exc

    payload = MemoryIngestRequest(
        user_id=user_id,
        original_filename=file.filename or safe_name,
        file_type=file_type,
        file_size_bytes=len(content),
        file_path=str(dest_path),
        chunks=chunks,
    )
    memory = await memory_service.ingest_memory_with_chunks(db, payload)
    return MemoryRead.model_validate(memory)


@router.post(
    "/ingest",
    response_model=MemoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a document with extracted chunks into vector memory",
)
async def ingest_memory(
    payload: MemoryIngestRequest,
    db: DatabaseSession,
) -> MemoryRead:
    """
    Ingest a document metadata record and its text chunks.
    Automatically generates embeddings for all chunks and persists to pgvector.
    """
    memory = await memory_service.ingest_memory_with_chunks(db, payload)
    return MemoryRead.model_validate(memory)


@router.get(
    "",
    response_model=MemoryListResponse,
    summary="List all memories for a user",
)
async def list_memories(
    user_id: Annotated[uuid.UUID, Query(description="User ID to filter memories")],
    db: DatabaseSession,
    skip: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Limit for pagination")] = 50,
) -> MemoryListResponse:
    """Retrieve all uploaded documents and their processing statuses for a user."""
    total, items = await memory_service.list_memories(
        db, user_id=user_id, skip=skip, limit=limit
    )
    return MemoryListResponse(
        total=total,
        items=[MemoryRead.model_validate(item) for item in items],
    )


@router.get(
    "/{memory_id}",
    response_model=MemoryRead,
    summary="Get memory document details",
)
async def get_memory_detail(
    memory_id: uuid.UUID,
    user_id: Annotated[
        uuid.UUID, Query(description="User ID for ownership verification")
    ],
    db: DatabaseSession,
) -> MemoryRead:
    """Get a specific memory document by its ID."""
    memory = await memory_service.get_memory(db, memory_id=memory_id, user_id=user_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory document not found or access denied.",
        )
    return MemoryRead.model_validate(memory)


@router.delete(
    "/{memory_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a memory document and its chunks",
)
async def delete_memory(
    memory_id: uuid.UUID,
    user_id: Annotated[
        uuid.UUID, Query(description="User ID for ownership verification")
    ],
    db: DatabaseSession,
) -> dict[str, bool]:
    """
    Delete a memory record.
    Cascades automatically to delete all linked chunks and vector embeddings.
    """
    deleted = await memory_service.delete_memory(
        db, memory_id=memory_id, user_id=user_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory document not found or access denied.",
        )
    return {"deleted": True}


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Perform semantic vector retrieval on user memories",
)
async def search_memories(
    payload: SearchRequest,
    db: DatabaseSession,
) -> SearchResponse:
    """
    Search chunks across all user documents using semantic vector similarity.
    Enforces strict tenant isolation to the requesting user_id.
    """
    results = await retrieval_service.search_memories(
        db=db,
        user_id=payload.user_id,
        query=payload.query,
        top_k=payload.top_k,
        min_similarity=payload.min_similarity,
    )
    return SearchResponse(
        query=payload.query,
        total_results=len(results),
        results=results,
    )
