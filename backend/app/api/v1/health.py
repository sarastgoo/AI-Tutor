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

@router.get("/health/full")
async def health_full(session: SessionDep) -> dict:
    """Comprehensive health check: DB, Ollama, models."""
    import httpx

    # DB
    db_ok = True
    db_error = None
    try:
        from sqlalchemy import text
        await session.execute(text("SELECT 1"))
    except Exception as e:
        db_ok = False
        db_error = str(e)

    # Ollama
    ollama_ok = True
    ollama_models = []
    ollama_error = None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            ollama_models = [m["name"] for m in data.get("models", [])]
    except Exception as e:
        ollama_ok = False
        ollama_error = str(e)

    return {
        "status": "ok" if db_ok and ollama_ok else "degraded",
        "db": {"ok": db_ok, "error": db_error},
        "ollama": {"ok": ollama_ok, "models": ollama_models, "error": ollama_error},
        "env": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
    }        