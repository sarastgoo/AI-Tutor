"""Retrieval endpoints for testing semantic search."""
from fastapi import APIRouter, HTTPException

from app.api.deps import SessionDep
from app.models.books import Book
from app.services.retrieval_service import RetrievalService
from sqlalchemy import select

router = APIRouter(tags=["retrieval"])


@router.get("/books/{book_id}/search")
async def search(
    book_id: str,
    q: str,
    session: SessionDep,
    top_k: int = 5,
) -> dict:
    """Semantic search within a book's chunks."""
    book = (
        await session.execute(select(Book).where(Book.id == book_id))
    ).scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    svc = RetrievalService(session)
    results = await svc.search(book_id=book_id, query=q, top_k=top_k)
    return {
        "book_id": book_id,
        "query": q,
        "count": len(results),
        "results": [r.to_dict() for r in results],
    }