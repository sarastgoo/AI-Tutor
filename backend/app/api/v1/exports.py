"""Exports endpoints."""
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.deps import SessionDep
from app.config import settings
from app.models.books import Book
from app.services.export_service import ExportService

router = APIRouter(tags=["exports"])


@router.post(
    "/books/{book_id}/export/vocabulary",
    status_code=status.HTTP_201_CREATED,
)
async def export_vocabulary(book_id: str, session: SessionDep) -> dict:
    """Generate a DOCX vocabulary export for a book."""
    book = (await session.execute(select(Book).where(Book.id == book_id))).scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    svc = ExportService(session)
    result = await svc.export_vocabulary_docx(book.id)
    path = Path(result.output_path)
    return {
        "book_id": str(book.id),
        "filename": path.name,
        "download_url": f"/api/v1/exports/download/{path.name}",
        **result.to_dict(),
    }


@router.get("/exports/download/{filename}")
async def download_export(filename: str) -> FileResponse:
    """Download a generated export file (loopback only)."""
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = settings.STORAGE_ROOT / "exports" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Export file not found")
    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if filename.endswith(".docx")
        else "application/octet-stream"
    )
    return FileResponse(str(path), media_type=media_type, filename=filename)