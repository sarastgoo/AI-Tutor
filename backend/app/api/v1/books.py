"""Books + ingestion endpoints."""
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep
from app.config import settings
from app.models.books import Book
from app.models.sources import SourceFile
from app.schemas.book import (
    BookCreate,
    BookResponse,
    IngestLocalRequest,
    IngestLocalResponse,
)
from app.services.ingestion_service import IngestionService

router = APIRouter(tags=["books"])


@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(body: BookCreate, session: SessionDep) -> Book:
    """Create a new book."""
    book = Book(**body.model_dump(), status="draft")
    session.add(book)
    await session.flush()
    await session.refresh(book)
    return book


@router.get("/books", response_model=list[BookResponse])
async def list_books(session: SessionDep) -> list[Book]:
    """List all books."""
    result = await session.execute(select(Book).order_by(Book.created_at.desc()))
    return list(result.scalars())


@router.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book_id: str, session: SessionDep) -> Book:
    """Get one book by ID."""
    result = await session.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post(
    "/books/{book_id}/import-local",
    response_model=IngestLocalResponse,
    status_code=status.HTTP_200_OK,
)
async def import_local(
    book_id: str,
    body: IngestLocalRequest,
    session: SessionDep,
) -> IngestLocalResponse:
    """Synchronously ingest a PDF from the allowlisted IMPORT_ROOT.

    NOTE: For P2 this is synchronous; will become a background job in P3.
    """
    result = await session.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    # Resolve and validate path
    root = settings.IMPORT_ROOT.resolve()
    pdf_path = (root / body.relative_path).resolve()
    try:
        pdf_path.relative_to(root)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path escapes IMPORT_ROOT")
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {pdf_path.name}")
    if pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only .pdf files are supported")

    svc = IngestionService(session)
    src = await svc.register_source_file(book, pdf_path)

    # Validate page range
    if body.page_end > (src.page_count or 0):
        raise HTTPException(
            status_code=400,
            detail=f"page_end ({body.page_end}) exceeds page_count ({src.page_count})",
        )

    t0 = time.time()
    total_blocks = 0
    pages_done = 0
    for pn in range(body.page_start, body.page_end):
        n = await svc.ingest_page(src, pdf_path, pn, dpi=body.dpi)
        total_blocks += n
        pages_done += 1

    elapsed = time.time() - t0

    # Update status
    book.status = "review_required"
    src.status = "ocr_completed"
    await session.flush()

    return IngestLocalResponse(
        source_file_id=src.id,
        pages_processed=pages_done,
        blocks_inserted=total_blocks,
        elapsed_s=round(elapsed, 2),
    )


@router.get("/books/{book_id}/sources")
async def list_sources(book_id: str, session: SessionDep) -> list[dict]:
    """List source files for a book."""
    result = await session.execute(
        select(SourceFile).where(SourceFile.book_id == book_id)
    )
    return [
        {
            "id": str(s.id),
            "relative_path": s.relative_path,
            "media_type": s.media_type,
            "page_count": s.page_count,
            "status": s.status,
            "sha256": s.sha256,
        }
        for s in result.scalars()
    ]