"""
Conversation repository — DB access for conversations and messages tables.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message

logger = logging.getLogger(__name__)


class ConversationRepository:
    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------
    def create_conversation(
        self, db: Session, user_id: int, title: str | None = None
    ) -> Conversation:
        conv = Conversation(user_id=user_id, title=title)
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    def get_conversation(self, db: Session, conversation_id: int) -> Conversation | None:
        return db.get(Conversation, conversation_id)

    def list_conversations(
        self, db: Session, user_id: int, skip: int = 0, limit: int = 50
    ) -> list[Conversation]:
        return list(
            db.execute(
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(Conversation.created_at.desc())
                .offset(skip)
                .limit(limit)
            ).scalars()
        )

    def delete_conversation(self, db: Session, conversation_id: int) -> bool:
        conv = self.get_conversation(db, conversation_id)
        if conv is None:
            return False
        db.delete(conv)
        db.commit()
        return True

    def update_title(
        self, db: Session, conversation_id: int, title: str
    ) -> Conversation | None:
        conv = self.get_conversation(db, conversation_id)
        if conv is None:
            return None
        conv.title = title
        db.commit()
        db.refresh(conv)
        return conv

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------
    def add_message(
        self,
        db: Session,
        conversation_id: int,
        role: str,
        content: str,
        sources: list | None = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    def get_messages(
        self, db: Session, conversation_id: int
    ) -> list[Message]:
        return list(
            db.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at)
            ).scalars()
        )


conversation_repository = ConversationRepository()
