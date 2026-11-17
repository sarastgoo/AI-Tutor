"""Audio ingestion endpoints."""
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import SessionDep
from app.config import settings
from app.models.audio import AudioSegment, AudioTrack
from app.models.books import Book
from app.models.sources import SourceFile
from app.schemas.audio import (
    AudioTrackResponse,
    TranscribeLocalRequest,
    TranscribeLocalResponse,
)
from app.services.ingestion_service import IngestionService

router = APIRouter(tags=["audio"])


@router.post(
    "/books/{book_id}/transcribe-local",
    response_model=TranscribeLocalResponse,
    status_code=status.HTTP_200_OK,
)
async def transcribe_local(
    book_id: str,
    body: TranscribeLocalRequest,
    session: SessionDep,
) -> TranscribeLocalResponse:
    """Synchronously transcribe an audio file from IMPORT_ROOT.

    NOTE: P3 synchronous; will become a background job in P4.
    """
    result = await session.execute(select(Book).where(Book.id == book_id))
    book = result.scalar_one_or_none()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    root = settings.IMPORT_ROOT.resolve()
    audio_path = (root / body.relative_path).resolve()
    try:
        audio_path.relative_to(root)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path escapes IMPORT_ROOT")
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {audio_path.name}")
    if audio_path.suffix.lower() not in (".mp3", ".wav", ".m4a", ".ogg"):
        raise HTTPException(status_code=400, detail="Unsupported audio format")

    svc = IngestionService(session)
    src = await svc.register_audio_file(book, audio_path)

    t0 = time.time()
    n_segments = await svc.ingest_audio(src, audio_path)
    elapsed = time.time() - t0

    # Find created track for response
    track_result = await session.execute(
        select(AudioTrack).where(AudioTrack.source_file_id == src.id)
    )
    track = track_result.scalar_one()

    return TranscribeLocalResponse(
        audio_track_id=track.id,
        segments_count=n_segments,
        duration_ms=src.duration_ms or 0,
        elapsed_s=round(elapsed, 2),
    )


@router.get("/audio/tracks/{track_id}/segments")
async def list_segments(track_id: str, session: SessionDep) -> list[dict]:
    """List all segments of an audio track."""
    result = await session.execute(
        select(AudioSegment)
        .where(AudioSegment.track_id == track_id)
        .order_by(AudioSegment.segment_index)
    )
    return [
        {
            "id": str(s.id),
            "segment_index": s.segment_index,
            "start_ms": s.start_ms,
            "end_ms": s.end_ms,
            "text": s.raw_transcript,
        }
        for s in result.scalars()
    ]