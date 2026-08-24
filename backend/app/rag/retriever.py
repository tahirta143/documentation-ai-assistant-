"""
Vector retriever — embeds the query and runs cosine similarity search via pgvector.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.embedding_service import embed_query

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: int
    document_id: int
    filename: str
    page_number: int | None
    chunk_index: int
    content: str
    score: float          # cosine similarity (0–1, higher = more similar)


def retrieve(
    db: Session,
    question: str,
    top_k: int | None = None,
    document_ids: list[int] | None = None,
) -> list[RetrievedChunk]:
    """Embed *question* and return the top-K most similar chunks.

    Args:
        db:           SQLAlchemy session.
        question:     The user's question string.
        top_k:        Number of chunks to return (defaults to settings.retrieval_top_k).
        document_ids: Optional list of document IDs to restrict search scope.

    Returns:
        List of RetrievedChunk sorted by similarity descending.
    """
    k = top_k or settings.retrieval_top_k

    # 1. Embed the question
    query_vector = embed_query(question)
    vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"

    # 2. Build the pgvector cosine similarity query
    #    <=> is the cosine distance operator; similarity = 1 - distance
    base_sql = """
        SELECT
            dc.id          AS chunk_id,
            dc.document_id,
            d.filename,
            dc.page_number,
            dc.chunk_index,
            dc.content,
            1 - (dc.embedding <=> CAST(:vec AS vector)) AS score
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE dc.embedding IS NOT NULL
    """

    params: dict = {"vec": vector_str, "k": k}

    if document_ids:
        base_sql += " AND dc.document_id = ANY(:doc_ids)"
        params["doc_ids"] = document_ids

    base_sql += " ORDER BY dc.embedding <=> CAST(:vec AS vector) LIMIT :k"

    rows = db.execute(text(base_sql), params).fetchall()

    chunks = [
        RetrievedChunk(
            chunk_id=row.chunk_id,
            document_id=row.document_id,
            filename=row.filename,
            page_number=row.page_number,
            chunk_index=row.chunk_index,
            content=row.content,
            score=float(row.score),
        )
        for row in rows
    ]

    logger.info(
        "Retrieved %d chunks for query (top_k=%d, min_score=%.3f)",
        len(chunks),
        k,
        min((c.score for c in chunks), default=0.0),
    )
    return chunks
