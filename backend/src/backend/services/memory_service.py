import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.chunk import Chunk
from backend.models.memory import Memory
from backend.models.user import User
from backend.schemas.memory import MemoryIngestRequest, MemoryStatus
from backend.services.embedding import BaseEmbeddingProvider, get_embedding_provider

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for managing memory records, file attachments, and vector chunks."""

    def __init__(self, embedding_provider: BaseEmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or get_embedding_provider()

    async def ensure_user_exists(
        self, db: AsyncSession, user_id: uuid.UUID, email: str | None = None
    ) -> User:
        """Helper to ensure a user record exists for foreign key constraints."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                id=user_id,
                email=email or f"user_{user_id.hex[:8]}@example.com",
            )
            db.add(user)
            await db.flush()
        return user

    async def ingest_memory_with_chunks(
        self,
        db: AsyncSession,
        payload: MemoryIngestRequest,
    ) -> Memory:
        """
        Store a document memory and generate vector embeddings for all its chunks.
        """
        # Ensure user exists for foreign key validity
        await self.ensure_user_exists(db, payload.user_id)

        # 1. Create Memory record
        memory = Memory(
            id=uuid.uuid4(),
            user_id=payload.user_id,
            original_filename=payload.original_filename,
            file_type=payload.file_type,
            file_path=payload.file_path,
            file_size_bytes=payload.file_size_bytes,
            status=MemoryStatus.PROCESSING.value,
            meta_info=payload.meta_info,
        )
        db.add(memory)
        await db.flush()

        # 2. Generate vector embeddings for all chunks in batch
        if payload.chunks:
            chunk_texts = [c.content for c in payload.chunks]
            embeddings = await self.embedding_provider.embed_batch(chunk_texts)

            for i, chunk_in in enumerate(payload.chunks):
                chunk = Chunk(
                    id=uuid.uuid4(),
                    memory_id=memory.id,
                    user_id=payload.user_id,
                    chunk_index=chunk_in.chunk_index,
                    content=chunk_in.content,
                    page_number=chunk_in.page_number,
                    embedding=embeddings[i] if i < len(embeddings) else None,
                    chunk_metadata=chunk_in.chunk_metadata,
                )
                db.add(chunk)

        memory.status = MemoryStatus.PROCESSED.value
        await db.commit()
        await db.refresh(memory)

        logger.info(
            "Ingested memory '%s' (%s) with %d chunks for user %s",
            memory.original_filename,
            memory.id,
            len(payload.chunks),
            payload.user_id,
        )
        return memory

    async def get_memory(
        self,
        db: AsyncSession,
        memory_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Memory | None:
        """Fetch a specific memory record belonging to the user."""
        stmt = (
            select(Memory)
            .where(Memory.id == memory_id)
            .where(Memory.user_id == user_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_memories(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[int, list[Memory]]:
        """List all memories belonging to the user with total count."""
        count_stmt = select(func.count(Memory.id)).where(Memory.user_id == user_id)
        total_count = (await db.execute(count_stmt)).scalar() or 0

        list_stmt = (
            select(Memory)
            .where(Memory.user_id == user_id)
            .order_by(Memory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(list_stmt)
        items = list(result.scalars().all())

        return total_count, items

    async def delete_memory(
        self,
        db: AsyncSession,
        memory_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """
        Delete a memory document.
        Cascading foreign keys in the DB automatically delete all associated chunks and vectors.
        """
        memory = await self.get_memory(db, memory_id, user_id)
        if not memory:
            return False

        await db.delete(memory)
        await db.commit()
        logger.info("Deleted memory %s and its chunks for user %s", memory_id, user_id)
        return True


memory_service = MemoryService()
