"""Pydantic DTOs for libraries."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class LibraryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    root_path: str = Field(..., min_length=1, max_length=1000)


class LibraryResponse(BaseModel):
    id: uuid.UUID
    name: str
    root_path: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScannedFileDTO(BaseModel):
    path: str
    relative_path: str
    media_type: str
    size_bytes: int


class ScanResponse(BaseModel):
    library_id: uuid.UUID
    root_path: str
    total_files: int
    pdf_files: int
    audio_files: int
    files: list[ScannedFileDTO]