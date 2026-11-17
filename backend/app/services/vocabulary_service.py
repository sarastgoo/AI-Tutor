"""Vocabulary Service: extract lexemes and occurrences from content blocks."""
import uuid
from dataclasses import dataclass
from typing import Any

import spacy
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import ContentBlock
from app.models.vocabulary import Lexeme, VocabularyOccurrence


@dataclass
class TokenOccurrence:
    """One token occurrence extracted from a text."""
    token_index: int
    surface_form: str
    normalized_form: str
    lemma: str
    pos: str


class VocabularyService:
    """Extracts lexemes and occurrences from validated content blocks."""

    _nlp = None  # Lazy-loaded spaCy model

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        if VocabularyService._nlp is None:
            VocabularyService._nlp = spacy.load("en_core_web_sm")

    @property
    def nlp(self):
        return VocabularyService._nlp

    def extract_tokens(self, text: str) -> list[TokenOccurrence]:
        """Tokenize text and return token occurrences with lemmas and POS."""
        doc = self.nlp(text)
        tokens: list[TokenOccurrence] = []
        for idx, token in enumerate(doc):
            # Skip punctuation, spaces, symbols, numbers
            if token.is_punct or token.is_space or token.is_digit or token.like_num:
                continue
            # Keep only alphabetic tokens (words)
            if not token.is_alpha:
                continue
            tokens.append(
                TokenOccurrence(
                    token_index=idx,
                    surface_form=token.text,
                    normalized_form=token.text.lower(),
                    lemma=token.lemma_.lower(),
                    pos=token.pos_,
                )
            )
        return tokens

    async def get_or_create_lexeme(
        self, lemma: str, pos: str, language: str = "en"
    ) -> Lexeme:
        """Find or create a lexeme for the given lemma + POS."""
        stmt = select(Lexeme).where(
            Lexeme.language == language,
            Lexeme.lemma == lemma,
            Lexeme.pos == pos,
            Lexeme.sense_key == "unspecified",
        )
        result = await self._session.execute(stmt)
        lexeme = result.scalar_one_or_none()
        if lexeme is None:
            lexeme = Lexeme(
                language=language,
                lemma=lemma,
                pos=pos,
                sense_key="unspecified",
                enrichment_status="pending",
            )
            self._session.add(lexeme)
            await self._session.flush()
        return lexeme

    async def extract_from_block(self, block: ContentBlock) -> int:
        """Extract vocabulary from one content block. Returns count of occurrences."""
        text = block.corrected_text or block.raw_text
        if not text or not text.strip():
            return 0

        tokens = self.extract_tokens(text)
        if not tokens:
            return 0

        # We need a SourceSpan to attach occurrences to.
        # In P2 we didn't create SourceSpans yet — create them here.
        # For simplicity, create one SourceSpan per content block.
        from app.models.content import SourceSpan

        stmt = select(SourceSpan).where(SourceSpan.content_block_id == block.id)
        result = await self._session.execute(stmt)
        span = result.scalar_one_or_none()
        if span is None:
            span = SourceSpan(
                content_block_id=block.id,
                start_offset=0,
                end_offset=len(text),
                source_version=block.text_version,
            )
            self._session.add(span)
            await self._session.flush()

        # Extract and persist
        count = 0
        for tok in tokens:
            lexeme = await self.get_or_create_lexeme(tok.lemma, tok.pos)
            occ = VocabularyOccurrence(
                source_span_id=span.id,
                lexeme_id=lexeme.id,
                surface_form=tok.surface_form,
                token_index=tok.token_index,
                normalized_form=tok.normalized_form,
                review_status="pending",
            )
            self._session.add(occ)
            count += 1

        await self._session.flush()
        return count

    async def extract_from_book(
        self, book_id: uuid.UUID, limit: int | None = None
    ) -> dict[str, Any]:
        """Extract vocabulary from all content blocks of a book."""
        from app.models.sources import SourceFile

        # Get all source files for the book (PDFs only)
        stmt = (
            select(ContentBlock)
            .join(SourceFile, SourceFile.id == ContentBlock.source_file_id)
            .where(SourceFile.book_id == book_id)
            .order_by(ContentBlock.source_file_id, ContentBlock.page_number, ContentBlock.block_order)
        )
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        blocks = list(result.scalars())

        total_occurrences = 0
        processed_blocks = 0
        for block in blocks:
            n = await self.extract_from_block(block)
            total_occurrences += n
            processed_blocks += 1

        return {
            "processed_blocks": processed_blocks,
            "total_occurrences": total_occurrences,
        }