# Architecture

## MVP flow

    Upload PDF or text
            ↓
    FastAPI validates and stores the source file
            ↓
    Extraction and chunking
            ↓
    Embedding generation
            ↓
    PostgreSQL + pgvector
            ↓
    Search relevant chunks
            ↓
    Grounded answer with sources

## Components

- **Mobile:** Flutter, Riverpod, and Dio.
- **Backend:** FastAPI, Pydantic, SQLAlchemy async, Alembic, and uv.
- **Database:** PostgreSQL with pgvector.
- **Testing:** pytest, HTTPX, Flutter tests, and end-to-end manual testing.
- **Local infrastructure:** Docker Compose.

## Data ownership

- A user owns many memories/documents.
- A memory has source metadata and an original stored file.
- A memory produces many chunks.
- Each chunk stores source metadata and one embedding.
- Retrieval must always filter results to the authenticated user.

## Non-goals for the first MVP

- Audio transcription
- Image OCR
- Hybrid search and reranking
- Complex memory editing
- Production deployment
