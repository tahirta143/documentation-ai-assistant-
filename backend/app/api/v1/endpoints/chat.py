"""
Chat endpoints.

POST   /api/chat                        — ask a question, get RAG answer
GET    /api/conversations               — list conversations
GET    /api/conversations/{id}          — get conversation with full message history
DELETE /api/conversations/{id}          — delete a conversation
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_db
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
) -> ChatResponse:
    """
    Send a question. The system will:
    1. Embed the question.
    2. Retrieve the most relevant document chunks via pgvector.
    3. Pass context + question to the LLM (answers only from your docs).
    4. Return the answer with source citations.

    Set `conversation_id` to continue an existing conversation,
    or leave it null to start a new one.
    Set `document_ids` to restrict retrieval to specific documents.
    """
    return chat_service.chat(db=db, request=request)


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
    summary="List all conversations",
)
def list_conversations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[ConversationResponse]:
    return chat_service.list_conversations(db=db, skip=skip, limit=limit)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get a conversation with full message history",
)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> ConversationDetailResponse:
    return chat_service.get_conversation(db=db, conversation_id=conversation_id)


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation and all its messages",
)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
) -> None:
    chat_service.delete_conversation(db=db, conversation_id=conversation_id)
