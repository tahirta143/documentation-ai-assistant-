"""
Chunk repository — all raw DB access for the document_chunks table.

Keeps SQL/ORM concerns out of the service layer.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk
from app.rag.chunker import TextChunk

logger = logging.getLogger(__name__)


class ChunkRepository:
    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    def bulk_create(
        self,
        db: Session,
        document_id: int,
        chunks: list[TextChunk],
    ) -> list[DocumentChunk]:
        """Insert all chunks for a document in a single transaction.

        Returns the persisted ORM objects (without embeddings yet).
        """
        if not chunks:
            return []

        orm_chunks = [
            DocumentChunk(
                document_id=document_id,
                content=c.content,
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                embedding=None,  # filled in Phase 7
            )
            for c in chunks
        ]

        db.add_all(orm_chunks)
        db.commit()

        # Refresh to populate server-generated fields (id, created_at)
        for ch in orm_chunks:
            db.refresh(ch)

        logger.info(
            "Inserted %d chunks for document_id=%d", len(orm_chunks), document_id
        )
        return orm_chunks

    def delete_by_document(self, db: Session, document_id: int) -> int:
        """Delete all chunks for a document. Returns number of rows deleted."""
        rows = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .all()
        )
        count = len(rows)
        for row in rows:
            db.delete(row)
        db.commit()
        logger.info("Deleted %d chunks for document_id=%d", count, document_id)
        return count

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    def get_by_document(
        self,
        db: Session,
        document_id: int,
    ) -> list[DocumentChunk]:
        """Return all chunks for a document ordered by chunk_index."""
        return list(
            db.execute(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == document_id)
                .order_by(DocumentChunk.chunk_index)
            ).scalars()
        )

    def get_by_id(self, db: Session, chunk_id: int) -> DocumentChunk | None:
        return db.get(DocumentChunk, chunk_id)


chunk_repository = ChunkRepository()
