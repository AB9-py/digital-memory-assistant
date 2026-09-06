from typing import Any

from fastapi import APIRouter, FastAPI

from backend.api.memories import router as memories_router
from backend.config import settings
from backend.database import check_db_connection

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for Digital Memory Assistant with pgvector semantic retrieval.",
)

# API v1 Router
api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(memories_router)

app.include_router(api_v1)


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
