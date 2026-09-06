import uuid

from pydantic import BaseModel, Field

from backend.config import settings
from backend.schemas.chunk import ChunkSearchResult


class SearchRequest(BaseModel):
    """Semantic vector search query request."""

    query: str = Field(..., min_length=1, description="Natural language search query")
    user_id: uuid.UUID = Field(..., description="User ID to isolate search scope")
    top_k: int = Field(
        default=settings.DEFAULT_TOP_K,
        ge=1,
        le=50,
        description="Maximum number of relevant chunks to retrieve",
    )
    min_similarity: float = Field(
        default=settings.DEFAULT_SIMILARITY_THRESHOLD,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity threshold (0.0 to 1.0)",
    )


class SearchResponse(BaseModel):
    """Semantic vector search response."""

    query: str
    total_results: int
    results: list[ChunkSearchResult]
