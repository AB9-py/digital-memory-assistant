from typing import Any

from fastapi import FastAPI

from backend.config import settings
from backend.database import check_db_connection

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for Digital Memory Assistant with pgvector semantic retrieval.",
)


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint returning system status."""
    db_connected = await check_db_connection()
    return {
        "status": "ok",
        "database": "connected" if db_connected else "disconnected",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
