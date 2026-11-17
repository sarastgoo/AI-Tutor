"""Health check endpoints."""
from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import SessionDep
from app.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Liveness check."""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/health/db")
async def health_db(session: SessionDep) -> dict:
    """Readiness check: verifies DB connectivity."""
    try:
        result = await session.execute(text("SELECT version()"))
        pg_version = result.scalar_one()
        # Verify pgvector is available
        ext = await session.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        )
        pgvector_version = ext.scalar_one_or_none()
        return {
            "status": "ok",
            "db": "connected",
            "postgres_version": pg_version.split()[0] if pg_version else None,
            "pgvector_version": pgvector_version,
        }
    except Exception as e:
        return {
            "status": "error",
            "db": "disconnected",
            "error": str(e),
        }