"""Export Service: generate DOCX vocabulary exports."""
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.books import Book
from app.models.content import ContentBlock, SourceSpan
from app.models.sources import SourceFile
from app.models.vocabulary import Lexeme, VocabularyOccurrence


@dataclass
class ExportResult:
    output_path: str
    total_lexemes: int
    total_occurrences: int
    elapsed_s: float

    def to_dict(self) -> dict:
        return {
            "output_path": self.output_path,
            "total_lexemes": self.total_lexemes,
            "total_occurrences": self.total_occurrences,
            "elapsed_s": round(self.elapsed_s, 2),
        }


class ExportService:
    """Generates DOCX vocabulary exports with source references."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def export_vocabulary_docx(
        self, book_id: uuid.UUID, out_dir: Path | None = None
    ) -> ExportResult:
        import time
        t0 = time.time()

        # 1. Load book
        book = (
            await self._session.execute(select(Book).where(Book.id == book_id))
        ).scalar_one_or_none()
        if book is None:
            raise ValueError(f"Book not found: {book_id}")

        # 2. Load all lexemes with occurrence counts (complete scan, per spec)
        lexeme_stmt = (
            select(
                Lexeme.id,
                Lexeme.lemma,
                Lexeme.pos,
                Lexeme.ipa,
                Lexeme.persian_meaning,
                func.count(VocabularyOccurrence.id).label("count"),
            )
            .join(VocabularyOccurrence, VocabularyOccurrence.lexeme_id == Lexeme.id)
            .join(SourceSpan, SourceSpan.id == VocabularyOccurrence.source_span_id)
            .join(ContentBlock, ContentBlock.id == SourceSpan.content_block_id)
            .join(SourceFile, SourceFile.id == ContentBlock.source_file_id)
            .where(SourceFile.book_id == book_id)
            .group_by(Lexeme.id, Lexeme.lemma, Lexeme.pos, Lexeme.ipa, Lexeme.persian_meaning)
            .order_by(func.count(VocabularyOccurrence.id).desc(), Lexeme.lemma)
        )
        rows = (await self._session.execute(lexeme_stmt)).all()

        total_occurrences = sum(r.count for r in rows)

        # 3. Build DOCX
        doc = Document()
        doc.add_heading(f"Vocabulary Export — {book.title}", level=1)
        doc.add_paragraph(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        doc.add_paragraph(f"Total lexemes: {len(rows)} | Total occurrences: {total_occurrences}")

        # Table
        table = doc.add_table(rows=1, cols=5)
        table.style = "Light Grid Accent 1"
        hdr = table.rows[0].cells
        hdr[0].text = "#"
        hdr[1].text = "Lemma"
        hdr[2].text = "POS"
        hdr[3].text = "Occurrences"
        hdr[4].text = "Persian Meaning"

        for idx, r in enumerate(rows, start=1):
            row = table.add_row().cells
            row[0].text = str(idx)
            row[1].text = r.lemma
            row[2].text = r.pos
            row[3].text = str(r.count)
            row[4].text = r.persian_meaning or "—"

        # Footer
        doc.add_paragraph()
        footer = doc.add_paragraph(
            "Note: This export includes all extracted vocabulary from the book's "
            "processed pages. Unresolved/uncertain tokens may be missing. "
            "Source references and OCR versions are recorded in the database."
        )
        footer.runs[0].italic = True
        footer.runs[0].font.size = Pt(9)

        # 4. Save
        out_dir = out_dir or Path(r"C:\Projects\ai-english-tutor\storage\exports")
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"vocab_{book_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        out_path = out_dir / filename
        doc.save(str(out_path))

        elapsed = time.time() - t0
        return ExportResult(
            output_path=str(out_path),
            total_lexemes=len(rows),
            total_occurrences=total_occurrences,
            elapsed_s=elapsed,
        )