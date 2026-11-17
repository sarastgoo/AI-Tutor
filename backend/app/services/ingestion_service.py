"""Ingestion Service: persist PDF + OCR results to the database."""
import hashlib
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.books import Book
from app.models.content import ContentBlock
from app.models.sources import SourceFile
from app.services.ocr_service import OCRService


class IngestionService:
    """Handles persisting source files and OCR results."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._ocr = None

    def _get_ocr(self) -> OCRService:
        """Lazy-init OCR (expensive to load)."""
        if self._ocr is None:
            self._ocr = OCRService(lang="en")
        return self._ocr

    @staticmethod
    def _sha256_file(path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    async def get_or_create_book(self, title: str, language: str = "en") -> Book:
        """Find or create a book by title."""
        stmt = select(Book).where(Book.title == title)
        result = await self._session.execute(stmt)
        book = result.scalar_one_or_none()
        if book is None:
            book = Book(title=title, language=language, status="processing")
            self._session.add(book)
            await self._session.flush()
        return book

    async def register_source_file(
        self, book: Book, pdf_path: Path, relative_path: str | None = None
    ) -> SourceFile:
        """Register a PDF as a source file (deduplicated by SHA-256)."""
        sha = self._sha256_file(pdf_path)
        rel = relative_path or pdf_path.name

        # Check for existing file with same hash in the same book
        stmt = select(SourceFile).where(
            SourceFile.book_id == book.id,
            SourceFile.sha256 == sha,
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing

        # Import pymupdf here to count pages
        import pymupdf
        doc = pymupdf.open(pdf_path)
        page_count = doc.page_count
        doc.close()

        src = SourceFile(
            book_id=book.id,
            relative_path=rel,
            media_type="application/pdf",
            sha256=sha,
            page_count=page_count,
            status="ocr_pending",
        )
        self._session.add(src)
        await self._session.flush()
        return src

    async def ingest_page(
        self,
        source_file: SourceFile,
        pdf_path: Path,
        page_num: int,
        dpi: int = 250,
    ) -> int:
        """Run OCR on one page and persist ContentBlocks. Returns block count."""
        ocr = self._get_ocr()
        result = ocr.process_page(pdf_path, page_num, dpi=dpi)

        # Persist each block
        count = 0
        for order, block in enumerate(result.blocks):
            if block.confidence < 0.3:
                # Skip very low confidence noise (can be tuned in P2 review)
                continue
            cb = ContentBlock(
                source_file_id=source_file.id,
                page_number=result.page_number,
                block_order=order,
                block_type="text",
                bbox={"polygon": block.bbox},
                raw_text=block.text,
                corrected_text=None,
                text_version=1,
                ocr_confidence=block.confidence,
                review_status="pending",
            )
            self._session.add(cb)
            count += 1

        await self._session.flush()
        return count