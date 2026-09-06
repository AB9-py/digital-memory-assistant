import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.schemas.memory import (
    MemoryIngestRequest,
    MemoryListResponse,
    MemoryRead,
)
from backend.schemas.search import SearchRequest, SearchResponse
from backend.services.memory_service import memory_service
from backend.services.retrieval_service import retrieval_service

router = APIRouter(prefix="/memories", tags=["memories"])

DatabaseSession = Annotated[AsyncSession, Depends(get_db)]


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
