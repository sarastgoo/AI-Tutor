"""End-to-end ingestion test: PDF -> OCR -> Database."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from sqlalchemy import select, func

from app.db.session import session_context
from app.models.content import ContentBlock
from app.services.ingestion_service import IngestionService


async def main():
    pdf_path = Path(r"C:\Projects\ai-english-tutor\scripts\fixtures\Book.pdf")
    if not pdf_path.exists():
        print(f"ERROR: {pdf_path} not found")
        return 1

    print("Starting ingestion test (3 pages)...")
    async with session_context() as session:
        svc = IngestionService(session)

        # 1. Book
        book = await svc.get_or_create_book("AEF 2 Student's Book")
        print(f"Book: {book.title} (id={book.id})")

        # 2. Source file
        src = await svc.register_source_file(book, pdf_path)
        print(f"Source: {src.relative_path} ({src.page_count} pages, sha={src.sha256[:12]}...)")

        # 3. OCR + persist pages 0-2
        for pn in range(3):
            print(f"  Ingesting page {pn + 1}...", end="", flush=True)
            n = await svc.ingest_page(src, pdf_path, pn)
            print(f" {n} blocks persisted")

    # 4. Verify
    print("\nVerification:")
    async with session_context() as session:
        result = await session.execute(
            select(func.count(ContentBlock.id)).where(ContentBlock.source_file_id == src.id)
        )
        total = result.scalar()
        print(f"  Total content_blocks in DB: {total}")

        sample = await session.execute(
            select(ContentBlock)
            .where(ContentBlock.source_file_id == src.id)
            .order_by(ContentBlock.page_number, ContentBlock.block_order)
            .limit(5)
        )
        print("  First 5 blocks:")
        for cb in sample.scalars():
            print(f"    [p{cb.page_number}#{cb.block_order}] {cb.raw_text[:60]!r}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))