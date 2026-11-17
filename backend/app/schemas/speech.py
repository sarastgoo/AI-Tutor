"""Pydantic DTOs for speech."""
from pydantic import BaseModel, Field


class SynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class SynthesizeResponse(BaseModel):
    audio_id: str
    download_url: str
    size_bytes: int
    elapsed_s: float