"""Resize embedding column from 1536 to 384 dims for local sentence-transformers

Revision ID: 0002_resize_embedding_384
Revises: 0001_initial_schema
Create Date: 2026-09-22

"""

from collections.abc import Sequence

from pgvector.sqlalchemy import Vector
from alembic import op

revision: str = "0002_resize_embedding_384"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop the HNSW index first (can't ALTER a column that has a vector index)
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding_hnsw;")
    # Resize the vector column — clears any existing embeddings
    op.execute("ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(384);")
    # Recreate HNSW index at new dimension
    op.execute(
        "CREATE INDEX ix_chunks_embedding_hnsw ON chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunks_embedding_hnsw;")
    op.execute("ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(1536);")
    op.execute(
        "CREATE INDEX ix_chunks_embedding_hnsw ON chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);"
    )
