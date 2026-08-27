"""
Chat service — orchestrates the RAG pipeline, streaming, and persists Q&A to the DB.
"""

from __future__ import annotations

import logging
from collections.abc import Generator

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.rag.pipeline import (
    PipelineResult,
    run as run_pipeline,
    run_stream as run_pipeline_stream,
)
from app.repositories.conversation_repository import conversation_repository
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationDetailResponse,
    ConversationResponse,
    MessageResponse,
    SourceCitation,
)

logger = logging.getLogger(__name__)


class ChatService:
    def chat(
        self,
        db: Session,
        request: ChatRequest,
        user_id: int,
    ) -> ChatResponse:
        """Run RAG pipeline and persist the Q&A pair."""
        # ---- Get or create conversation --------------------------------
        if request.conversation_id is not None:
            conv = conversation_repository.get_conversation(
                db, request.conversation_id
            )
            if conv is None or conv.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {request.conversation_id} not found.",
                )
        else:
            title = request.question[:60] + ("…" if len(request.question) > 60 else "")
            conv = conversation_repository.create_conversation(
                db, user_id=user_id, title=title
            )
            logger.info("Created conversation id=%d for user_id=%d", conv.id, user_id)

        # ---- Persist the user message ----------------------------------
        conversation_repository.add_message(
            db,
            conversation_id=conv.id,
            role="user",
            content=request.question,
        )

        # ---- Run the RAG pipeline -------------------------------------
        result: PipelineResult = run_pipeline(
            db=db,
            question=request.question,
            document_ids=request.document_ids,
            user_id=user_id,
        )

        # ---- Persist the assistant message ----------------------------
        assistant_msg = conversation_repository.add_message(
            db,
            conversation_id=conv.id,
            role="assistant",
            content=result.answer,
            sources=result.sources,
        )
        logger.info(
            "Chat complete: conv_id=%d msg_id=%d chunks_used=%d",
            conv.id, assistant_msg.id, result.chunks_used,
        )

        return ChatResponse(
            answer=result.answer,
            conversation_id=conv.id,
            message_id=assistant_msg.id,
            sources=[SourceCitation(**s) for s in result.sources],
        )

    def chat_stream(
        self,
        db: Session,
        request: ChatRequest,
        user_id: int,
    ) -> Generator[str, None, None]:
        """Run RAG pipeline and yield SSE stream events."""
        # ---- Get or create conversation --------------------------------
        if request.conversation_id is not None:
            conv = conversation_repository.get_conversation(
                db, request.conversation_id
            )
            if conv is None or conv.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Conversation {request.conversation_id} not found.",
                )
        else:
            title = request.question[:60] + ("…" if len(request.question) > 60 else "")
            conv = conversation_repository.create_conversation(
                db, user_id=user_id, title=title
            )

        conversation_repository.add_message(
            db,
            conversation_id=conv.id,
            role="user",
            content=request.question,
        )

        return run_pipeline_stream(
            db=db,
            question=request.question,
            document_ids=request.document_ids,
            user_id=user_id,
        )

    def list_conversations(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ConversationResponse]:
        convs = conversation_repository.list_conversations(
            db, user_id=user_id, skip=skip, limit=limit
        )
        return [ConversationResponse.model_validate(c) for c in convs]

    def get_conversation(
        self, db: Session, conversation_id: int, user_id: int
    ) -> ConversationDetailResponse:
        conv = conversation_repository.get_conversation(db, conversation_id)
        if conv is None or conv.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found.",
            )
        messages = conversation_repository.get_messages(db, conversation_id)
        return ConversationDetailResponse(
            id=conv.id,
            user_id=conv.user_id,
            title=conv.title,
            created_at=conv.created_at,
            messages=[MessageResponse.model_validate(m) for m in messages],
        )

    def delete_conversation(self, db: Session, conversation_id: int, user_id: int) -> None:
        conv = conversation_repository.get_conversation(db, conversation_id)
        if conv is None or conv.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation {conversation_id} not found.",
            )
        conversation_repository.delete_conversation(db, conversation_id)


chat_service = ChatService()
