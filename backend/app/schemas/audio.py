"""Pydantic DTOs for audio ingestion."""
import uuid
from datetime import datetime

from pydantic import BaseModel


class AudioTrackResponse(BaseModel):
    id: uuid.UUID
    source_file_id: uuid.UUID
    label: str | None
    duration_ms: int
    transcription_status: str

    model_config = {"from_attributes": True}


class TranscribeLocalRequest(BaseModel):
    """Request to transcribe an audio file from IMPORT_ROOT."""
    relative_path: str


class TranscribeLocalResponse(BaseModel):
    audio_track_id: uuid.UUID
    segments_count: int
    duration_ms: int
    elapsed_s: float