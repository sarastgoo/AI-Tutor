"""Pydantic DTOs for tutor sessions."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    book_id: uuid.UUID
    active_node_id: uuid.UUID | None = None
    mode: str = Field("free", pattern="^(guided|free|review)$")


class SessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    book_id: uuid.UUID
    active_node_id: uuid.UUID | None
    mode: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


class SendMessageResponse(BaseModel):
    user_message_id: uuid.UUID
    assistant_message_id: uuid.UUID
    reply: str
    sources: list[dict]
    elapsed_s: float