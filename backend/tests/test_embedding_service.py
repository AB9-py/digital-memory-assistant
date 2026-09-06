import math

import pytest

from backend.services.embedding import (
    DeterministicEmbeddingProvider,
    get_embedding_provider,
)


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(v1, v2, strict=False))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product / (mag1 * mag2)


@pytest.mark.anyio
async def test_deterministic_embedding_dimension_and_norm() -> None:
    provider = DeterministicEmbeddingProvider(dimension=1536)
    vec = await provider.embed_text("Operating system deadlock prevention")

    assert len(vec) == 1536
    # Verify unit norm
    norm = math.sqrt(sum(x * x for x in vec))
    assert pytest.approx(norm, rel=1e-3) == 1.0


@pytest.mark.anyio
async def test_deterministic_embedding_consistency() -> None:
    provider = DeterministicEmbeddingProvider(dimension=1536)
    vec1 = await provider.embed_text("Virtual memory management")
    vec2 = await provider.embed_text("Virtual memory management")

    assert vec1 == vec2


@pytest.mark.anyio
async def test_deterministic_embedding_semantic_ranking() -> None:
    provider = DeterministicEmbeddingProvider(dimension=1536)

    query = await provider.embed_text("deadlock prevention")
    related = await provider.embed_text("deadlock prevention in operating systems")
    unrelated = await provider.embed_text("recipe for chocolate chip cookies")

    sim_related = cosine_similarity(query, related)
    sim_unrelated = cosine_similarity(query, unrelated)

    assert sim_related > sim_unrelated


@pytest.mark.anyio
async def test_deterministic_embedding_batch() -> None:
    provider = DeterministicEmbeddingProvider(dimension=1536)
    texts = ["Page table", "Kernel architecture", "Scheduling algorithms"]

    batch_vecs = await provider.embed_batch(texts)
    assert len(batch_vecs) == 3

    for i, text in enumerate(texts):
        single_vec = await provider.embed_text(text)
        assert batch_vecs[i] == single_vec


def test_get_embedding_provider_factory() -> None:
    provider = get_embedding_provider()
    assert provider is not None
