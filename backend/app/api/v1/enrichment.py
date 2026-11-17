"""Enrichment endpoints."""
from fastapi import APIRouter

from app.api.deps import SessionDep
from app.services.enrichment_service import EnrichmentService

router = APIRouter(tags=["enrichment"])


@router.post("/enrichment/run")
async def run_enrichment(session: SessionDep, limit: int = 20) -> dict:
    """Enrich up to `limit` lexemes (synchronous, but for small batches)."""
    svc = EnrichmentService(session)
    result = await svc.enrich_lexemes(limit=limit)
    return {
        "processed": result.processed,
        "enriched": result.enriched,
        "elapsed_s": round(result.elapsed_s, 2),
    }