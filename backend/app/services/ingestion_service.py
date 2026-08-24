"""
Ingestion service — orchestrates the full document ingestion pipeline.

Pipeline:
  1. Load & extract text  (loaders/)
  2. Clean text           (utils/text_cleaner)
  3. Chunk into windows   (rag/chunker)
  4. Store chunks in DB   (repositories/chunk_repository)
  5. Generate + store embeddings per chunk (services/embedding_service)
  6. Update document status → ready | failed
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.loaders import load_document
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.rag.chunker import chunk_pages
from app.repositories.chunk_repository import chunk_repository
from app.repositories.document_repository import document_repository

logger = logging.getLogger(__name__)


class IngestionService:
    def ingest(self, db: Session, doc: Document) -> None:
        """Run the full ingestion pipeline for *doc*.

        Mutates doc.status in-place and persists it.
        Idempotent — old chunks are deleted before re-inserting.
        """
        logger.info("Starting ingestion for document id=%d (%s)", doc.id, doc.filename)

        try:
            # ---------------------------------------------------------- #
            # Step 1 + 2: load and clean                                  #
            # ---------------------------------------------------------- #
            loaded = load_document(doc.file_path, doc.file_type)

            if not loaded.full_text.strip():
                logger.warning("Document id=%d produced no extractable text", doc.id)
                document_repository.update_status(db, doc.id, "failed")
                doc.status = "failed"
                return

            logger.info(
                "Loaded document id=%d | pages=%d | chars=%d",
                doc.id, len(loaded.pages), len(loaded.full_text),
            )

            # ---------------------------------------------------------- #
            # Step 3: chunk                                                #
            # ---------------------------------------------------------- #
            chunks = chunk_pages(
                pages=loaded.pages,
                chunk_size=settings.chunk_size,
                overlap=settings.chunk_overlap,
            )

            if not chunks:
                logger.warning("Document id=%d produced 0 chunks", doc.id)
                document_repository.update_status(db, doc.id, "failed")
                doc.status = "failed"
                return

            logger.info("Chunked document id=%d → %d chunks", doc.id, len(chunks))

            # ---------------------------------------------------------- #
            # Step 4: store chunks                                         #
            # ---------------------------------------------------------- #
            chunk_repository.delete_by_document(db, doc.id)
            orm_chunks: list[DocumentChunk] = chunk_repository.bulk_create(
                db, doc.id, chunks
            )

            # ---------------------------------------------------------- #
            # Step 5: generate and store embeddings                        #
            # ---------------------------------------------------------- #
            self._embed_and_store(db, orm_chunks)

            # ---------------------------------------------------------- #
            # Step 6: mark ready                                           #
            # ---------------------------------------------------------- #
            document_repository.update_status(db, doc.id, "ready")
            doc.status = "ready"
            logger.info("Ingestion complete for document id=%d — status=ready", doc.id)

        except Exception as exc:
            logger.error(
                "Ingestion failed for document id=%d: %s", doc.id, exc, exc_info=True
            )
            document_repository.update_status(db, doc.id, "failed")
            doc.status = "failed"

    def _embed_and_store(
        self, db: Session, orm_chunks: list[DocumentChunk]
    ) -> None:
        """Generate embeddings for all chunks and persist them."""
        from app.services.embedding_service import embed_texts

        texts = [c.content for c in orm_chunks]
        logger.info("Generating embeddings for %d chunks…", len(texts))

        vectors = embed_texts(texts)

        for chunk, vector in zip(orm_chunks, vectors):
            chunk.embedding = vector

        db.commit()
        logger.info("Stored %d embeddings", len(vectors))


ingestion_service = IngestionService()
