"""Pydantic DTOs for books and ingestion."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    edition: str | None = Field(None, max_length=100)
    level: str | None = Field(None, max_length=50)
    language: str = Field("en", max_length=10)


class BookResponse(BaseModel):
    id: uuid.UUID
    title: str
    edition: str | None
    level: str | None
    language: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IngestLocalRequest(BaseModel):
    """Request to ingest a PDF from an allowlisted local path."""
    relative_path: str = Field(..., description="Path under IMPORT_ROOT")
    page_start: int = Field(0, ge=0, description="0-based, inclusive")
    page_end: int = Field(3, ge=1, description="0-based, exclusive")
    dpi: int = Field(250, ge=150, le=400)


class IngestLocalResponse(BaseModel):
    source_file_id: uuid.UUID
    pages_processed: int
    blocks_inserted: int
    elapsed_s: float