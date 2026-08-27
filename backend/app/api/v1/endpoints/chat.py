"""
Chat endpoints (Secured with JWT authentication).

POST   /api/chat                        — ask a question, get RAG answer
POST   /api/chat/stream                 — ask a question, get SSE stream of answer
GET    /api/conversations               — list conversations
GET    /api/conversations/{id}          — get conversation with full message history
DELETE /api/conversations/{id}          — delete a conversation
"""

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationDetailResponse,
    ConversationResponse,
)
from app.services.chat_service import chat_service

router = APIRouter(tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question — get a RAG-grounded answer with source citations",
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """
    Send a question. The system will:
    1. Embed the question.
    2. Retrieve relevant document chunks owned by current user.
    3. Call LLM to ground the answer strictly in the context.
    4. Return the answer with source citations.
    """
    return chat_service.chat(db=db, request=request, user_id=current_user.id)


@router.post(
    "/chat/stream",
    summary="Ask a question — stream back tokens and citations in real time via SSE",
)
def chat_stream(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """
    Stream the answer token by token using Server-Sent Events (SSE).
    Each event data is a JSON object `{"token": "...", "done": bool, "sources": [...]}`.
    """
    generator = chat_service.chat_stream(
        db=db, request=request, user_id=current_user.id
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
    summary="List all conversations for current user",
)
def list_conversations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ConversationResponse]:
    return chat_service.list_conversations(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get a conversation with full message history",
)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationDetailResponse:
    return chat_service.get_conversation(
        db=db, conversation_id=conversation_id, user_id=current_user.id
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation and all its messages",
)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    chat_service.delete_conversation(
        db=db, conversation_id=conversation_id, user_id=current_user.id
    )
