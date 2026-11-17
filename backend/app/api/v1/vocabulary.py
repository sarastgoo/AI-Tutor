"""Vocabulary endpoints."""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.models.books import Book
from app.models.vocabulary import Lexeme, VocabularyOccurrence
from app.services.vocabulary_service import VocabularyService

router = APIRouter(tags=["vocabulary"])


@router.post(
    "/books/{book_id}/extract-vocabulary",
    status_code=status.HTTP_200_OK,
)
async def extract_vocabulary(book_id: str, session: SessionDep) -> dict:
    """Extract vocabulary from all content blocks of a book."""
    result = await session.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    svc = VocabularyService(session)
    stats = await svc.extract_from_book(book.id)
    return {"book_id": str(book.id), **stats}


@router.get("/books/{book_id}/vocabulary")
async def list_vocabulary(
    book_id: str,
    session: SessionDep,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """List lexemes with occurrence counts for a book."""
    # Count occurrences per lexeme in this book
    from app.models.content import ContentBlock, SourceSpan
    from app.models.sources import SourceFile

    stmt = (
        select(
            Lexeme.id,
            Lexeme.lemma,
            Lexeme.pos,
            func.count(VocabularyOccurrence.id).label("occurrence_count"),
        )
        .join(VocabularyOccurrence, VocabularyOccurrence.lexeme_id == Lexeme.id)
        .join(SourceSpan, SourceSpan.id == VocabularyOccurrence.source_span_id)
        .join(ContentBlock, ContentBlock.id == SourceSpan.content_block_id)
        .join(SourceFile, SourceFile.id == ContentBlock.source_file_id)
        .where(SourceFile.book_id == book_id)
        .group_by(Lexeme.id, Lexeme.lemma, Lexeme.pos)
        .order_by(func.count(VocabularyOccurrence.id).desc(), Lexeme.lemma)
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(stmt)).all()

    total = (
        await session.execute(
            select(func.count(func.distinct(Lexeme.id)))
            .select_from(Lexeme)
            .join(VocabularyOccurrence, VocabularyOccurrence.lexeme_id == Lexeme.id)
            .join(SourceSpan, SourceSpan.id == VocabularyOccurrence.source_span_id)
            .join(ContentBlock, ContentBlock.id == SourceSpan.content_block_id)
            .join(SourceFile, SourceFile.id == ContentBlock.source_file_id)
            .where(SourceFile.book_id == book_id)
        )
    ).scalar_one()

    return {
        "book_id": book_id,
        "total_lexemes": total,
        "items": [
            {
                "lexeme_id": str(r.id),
                "lemma": r.lemma,
                "pos": r.pos,
                "occurrence_count": r.occurrence_count,
            }
            for r in rows
        ],
    }


@router.get("/vocabulary/{lexeme_id}/occurrences")
async def list_occurrences(
    lexeme_id: str, session: SessionDep, limit: int = 20
) -> dict:
    """List occurrences of a specific lexeme."""
    stmt = (
        select(VocabularyOccurrence)
        .where(VocabularyOccurrence.lexeme_id == lexeme_id)
        .order_by(VocabularyOccurrence.id)
        .limit(limit)
    )
    result = await session.execute(stmt)
    occs = list(result.scalars())
    return {
        "lexeme_id": lexeme_id,
        "count": len(occs),
        "items": [
            {
                "id": str(o.id),
                "surface_form": o.surface_form,
                "normalized_form": o.normalized_form,
                "token_index": o.token_index,
                "review_status": o.review_status,
            }
            for o in occs
        ],
    }