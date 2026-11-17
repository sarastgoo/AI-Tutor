"""Embeddings endpoints."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.models.books import Book
from app.models.rag import DocumentChunk
from app.services.embedding_service import EmbeddingService

router = APIRouter(tags=["embeddings"])


@router.post(
    "/books/{book_id}/embed",
    status_code=status.HTTP_200_OK,
)
async def embed_book(book_id: str, session: SessionDep) -> dict:
    """Chunk and embed all content blocks of a book."""
    result = await session.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    svc = EmbeddingService(session)
    result_obj = await svc.embed_book(book.id)
    return {
        "book_id": str(book.id),
        "chunks_created": result_obj.chunks_created,
        "embeddings_created": result_obj.embeddings_created,
        "elapsed_s": round(result_obj.elapsed_s, 2),
    }


@router.get("/books/{book_id}/chunks")
async def list_chunks(
    book_id: str, session: SessionDep, limit: int = 10, offset: int = 0
) -> dict:
    """List document chunks for a book."""
    stmt = (
        select(DocumentChunk)
        .where(DocumentChunk.book_id == book_id)
        .order_by(DocumentChunk.created_at)
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    chunks = list(result.scalars())

    total = (
        await session.execute(
            select(func.count(DocumentChunk.id)).where(DocumentChunk.book_id == book_id)
        )
    ).scalar_one()

    return {
        "book_id": book_id,
        "total_chunks": total,
        "items": [
            {
                "chunk_id": str(c.id),
                "preview": c.content[:120] + ("..." if len(c.content) > 120 else ""),
                "length": len(c.content),
                "chunker_version": c.chunker_version,
            }
            for c in chunks
        ],
    }