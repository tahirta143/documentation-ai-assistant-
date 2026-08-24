from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SourceCitation(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    page_number: int | None = None
    chunk_index: int
    score: float


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    conversation_id: int | None = None   # None = start a new conversation
    document_ids: list[int] | None = None  # None = search all docs


class ChatResponse(BaseModel):
    answer: str
    conversation_id: int
    message_id: int
    sources: list[SourceCitation] = []


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    sources: Any | None = None
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str | None = None
    created_at: datetime


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse] = []
