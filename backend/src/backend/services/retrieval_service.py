import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.models.chunk import Chunk
from backend.models.memory import Memory
from backend.schemas.chunk import ChunkSearchResult
from backend.services.embedding import BaseEmbeddingProvider, get_embedding_provider

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service handling semantic vector search and chunk retrieval with pgvector."""

    def __init__(self, embedding_provider: BaseEmbeddingProvider | None = None) -> None:
        self.embedding_provider = embedding_provider or get_embedding_provider()

    async def search_memories(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        top_k: int = settings.DEFAULT_TOP_K,
        min_similarity: float = settings.DEFAULT_SIMILARITY_THRESHOLD,
    ) -> list[ChunkSearchResult]:
        """
        Execute semantic vector similarity search filtered to the specified user.

        Args:
            db: Active async database session.
            user_id: Target user ID to enforce strict tenant isolation.
            query: Natural language query string.
            top_k: Maximum number of chunks to return.
            min_similarity: Minimum cosine similarity score threshold (0.0 to 1.0).

        Returns:
            List of ChunkSearchResult items ordered by relevance.
        """
        if not query.strip():
            return []

        # 1. Generate query embedding
        query_vector = await self.embedding_provider.embed_text(query)

        # 2. Build vector search query using pgvector cosine_distance (<=>)
        # Cosine distance ranges from 0 (identical) to 2 (opposite).
        # Similarity = 1.0 - (distance / 1.0) for unit vectors (clamped to [0.0, 1.0]).
        cosine_dist = Chunk.embedding.cosine_distance(query_vector).label("distance")

        stmt = (
            select(
                Chunk,
                Memory.original_filename,
                cosine_dist,
            )
            .join(Memory, Chunk.memory_id == Memory.id)
            .where(Chunk.user_id == user_id)
            .where(Chunk.embedding.is_not(None))
            .order_by(cosine_dist.asc())
            .limit(top_k)
        )

        result = await db.execute(stmt)
        rows = result.all()

        search_results: list[ChunkSearchResult] = []
        for chunk, original_filename, distance in rows:
            # Convert cosine distance to cosine similarity
            # Since vectors are unit-normalized, cosine_distance = 1 - cosine_similarity
            raw_similarity = 1.0 - float(distance) if distance is not None else 0.0
            similarity_score = max(0.0, min(1.0, raw_similarity))

            if similarity_score < min_similarity:
                continue

            search_results.append(
                ChunkSearchResult(
                    chunk_id=chunk.id,
                    memory_id=chunk.memory_id,
                    original_filename=original_filename,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    similarity_score=round(similarity_score, 4),
                    chunk_metadata=chunk.chunk_metadata or {},
                )
            )

        logger.info(
            "Semantic retrieval query '%s' for user %s returned %d matches",
            query,
            user_id,
            len(search_results),
        )
        return search_results


retrieval_service = RetrievalService()
