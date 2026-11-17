"""Progress tracking endpoints."""
from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.models.learning import (
    ChatMessage,
    ExerciseAttempt,
    LearningProgress,
    LearningSession,
    SpeakingAttempt,
    VocabularyReview,
)
from app.models.vocabulary import Lexeme

router = APIRouter(tags=["progress"])


@router.get("/progress")
async def get_progress(session: SessionDep) -> dict:
    """Aggregate progress for the local user."""
    # Total sessions
    total_sessions = (
        await session.execute(select(func.count(LearningSession.id)))
    ).scalar_one()

    # Total messages
    total_messages = (
        await session.execute(select(func.count(ChatMessage.id)))
    ).scalar_one()

    # Total speaking attempts
    total_speaking = (
        await session.execute(select(func.count(SpeakingAttempt.id)))
    ).scalar_one()

    # Total exercise attempts (future)
    total_exercises = (
        await session.execute(select(func.count(ExerciseAttempt.id)))
    ).scalar_one()

    # Total lexemes (unique vocabulary seen)
    total_lexemes = (await session.execute(select(func.count(Lexeme.id)))).scalar_one()

    # Due reviews
    due_reviews = (
        await session.execute(
            select(func.count(VocabularyReview.lexeme_id)).where(
                VocabularyReview.due_at <= func.now()
            )
        )
    ).scalar_one()

    return {
        "sessions": total_sessions,
        "messages": total_messages,
        "speaking_attempts": total_speaking,
        "exercise_attempts": total_exercises,
        "unique_lexemes": total_lexemes,
        "due_reviews": due_reviews,
    }


@router.get("/progress/sessions")
async def list_sessions(session: SessionDep, limit: int = 20) -> dict:
    """List recent learning sessions."""
    stmt = select(LearningSession).order_by(LearningSession.created_at.desc()).limit(limit)
    rows = list((await session.execute(stmt)).scalars())
    return {
        "count": len(rows),
        "items": [
            {
                "id": str(s.id),
                "book_id": str(s.book_id),
                "mode": s.mode,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
            }
            for s in rows
        ],
    }