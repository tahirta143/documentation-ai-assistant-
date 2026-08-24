from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# pgvector's Vector type — imported lazily so the app can still start
# even if the pgvector extension is not yet enabled in the database.
try:
    from pgvector.sqlalchemy import Vector
    _VECTOR_TYPE = Vector(1536)   # default dimension for text-embedding-3-small
except ImportError:
    # Fallback: store embeddings as plain Text (dev / no-pgvector environment).
    # Replace with Vector once pgvector is installed.
    from sqlalchemy import Text as _VectorFallback  # type: ignore[assignment]
    _VECTOR_TYPE = _VectorFallback()


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Vector column — 1536-dim float32 (matches OpenAI text-embedding-3-small).
    # Dimension must match EMBEDDING_DIMENSION in config; change here + re-migrate
    # if you switch models.
    embedding: Mapped[None] = mapped_column(_VECTOR_TYPE, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")

    def __repr__(self) -> str:
        return (
            f"<DocumentChunk id={self.id} doc={self.document_id} "
            f"idx={self.chunk_index}>"
        )
