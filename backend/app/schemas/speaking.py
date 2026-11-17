"""Pydantic DTOs for speaking attempts."""
import uuid
from datetime import datetime

from pydantic import BaseModel


class SpeakingAttemptResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    recording_path: str
    transcript: str | None
    stt_profile: str | None
    feedback: dict
    pronunciation_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SpeakingAttemptDetail(BaseModel):
    id: uuid.UUID
    transcript: str
    feedback_text: str
    reply_text: str | None = None
    reply_audio_url: str | None = None
    pronunciation_status: str