# Re-export all models so a single import registers them all on Base.metadata.
# Usage:  from app.models import User, Document, DocumentChunk, Conversation, Message
from app.models.chunk import DocumentChunk
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.message import Message
from app.models.user import User

__all__ = ["User", "Document", "DocumentChunk", "Conversation", "Message"]
