import hashlib
import logging
import math
from abc import ABC, abstractmethod
from typing import Any

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


class BaseEmbeddingProvider(ABC):
    """Abstract base class for vector embedding generation."""

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """Generate vector embedding for a single text string."""

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate vector embeddings for a list of text strings."""


class DeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic pseudo-semantic embedding generator for testing and local dev.

    Generates unit-normalized float vectors using character and n-gram hash
    projections into the configured embedding dimension.
    """

    def __init__(self, dimension: int = settings.EMBEDDING_DIM) -> None:
        self.dimension = dimension

    def _generate_vector(self, text: str) -> list[float]:
        if not text:
            return [0.0] * self.dimension

        vector = [0.0] * self.dimension
        words = text.lower().split()
        for i, word in enumerate(words):
            word_hash = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx = word_hash % self.dimension
            weight = 1.0 / math.sqrt(i + 1)
            vector[idx] += weight

            # Also hash character bigrams for subword similarity
            for j in range(len(word) - 1):
                bigram = word[j : j + 2]
                bg_hash = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16)
                bg_idx = bg_hash % self.dimension
                vector[bg_idx] += 0.2

        # L2-normalize the vector
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            return [v / magnitude for v in vector]
        return vector

    async def embed_text(self, text: str) -> list[float]:
        return self._generate_vector(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._generate_vector(t) for t in texts]


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Generates vector embeddings using OpenAI's embeddings API."""

    def __init__(
        self,
        api_key: str,
        model: str = settings.EMBEDDING_MODEL,
        dimension: int = settings.EMBEDDING_DIM,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.dimension = dimension
        self.api_url = "https://api.openai.com/v1/embeddings"

    async def _call_api(self, input_payload: list[str]) -> list[list[float]]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        json_data: dict[str, Any] = {
            "input": input_payload,
            "model": self.model,
        }
        if "text-embedding-3" in self.model:
            json_data["dimensions"] = self.dimension

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.api_url, headers=headers, json=json_data)
            response.raise_for_status()
            data = response.json()
            # Sort by index to ensure matching order
            sorted_data = sorted(data["data"], key=lambda item: item["index"])
            return [item["embedding"] for item in sorted_data]

    async def embed_text(self, text: str) -> list[float]:
        results = await self._call_api([text])
        return results[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await self._call_api(texts)


_provider_instance: BaseEmbeddingProvider | None = None


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Dependency / factory returning the configured embedding provider."""
    global _provider_instance
    if _provider_instance is None:
        if settings.EMBEDDING_PROVIDER.lower() == "openai" and settings.OPENAI_API_KEY:
            _provider_instance = OpenAIEmbeddingProvider(
                api_key=settings.OPENAI_API_KEY,
                model=settings.EMBEDDING_MODEL,
                dimension=settings.EMBEDDING_DIM,
            )
            logger.info(
                "Initialized OpenAIEmbeddingProvider (%s)", settings.EMBEDDING_MODEL
            )
        else:
            _provider_instance = DeterministicEmbeddingProvider(
                dimension=settings.EMBEDDING_DIM
            )
            logger.info(
                "Initialized DeterministicEmbeddingProvider (dim=%s)",
                settings.EMBEDDING_DIM,
            )
    return _provider_instance
