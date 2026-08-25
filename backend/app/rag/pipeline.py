"""
RAG pipeline — wires together retrieval + LLM answer generation.

Flow:
  question → embed → vector search → build context → call LLM → answer + sources
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.config import settings
from app.rag.prompts import SYSTEM_PROMPT, build_prompt
from app.rag.retriever import RetrievedChunk, retrieve

logger = logging.getLogger(__name__)

_NO_CONTEXT_ANSWER = "I don't have this information in the documentation."


@dataclass
class PipelineResult:
    answer: str
    sources: list[dict] = field(default_factory=list)
    chunks_used: int = 0


def run(
    db: Session,
    question: str,
    top_k: int | None = None,
    document_ids: list[int] | None = None,
) -> PipelineResult:
    """Run the full RAG pipeline for a question.

    Args:
        db:           Active SQLAlchemy session.
        question:     The user's question.
        top_k:        Override default retrieval count.
        document_ids: Restrict retrieval to specific documents.

    Returns:
        PipelineResult with answer text and source citations.
    """
    # ------------------------------------------------------------------ #
    # 1. Retrieve relevant chunks                                          #
    # ------------------------------------------------------------------ #
    chunks: list[RetrievedChunk] = retrieve(
        db=db, question=question, top_k=top_k, document_ids=document_ids
    )

    if not chunks:
        logger.info("No chunks retrieved — returning no-context answer")
        return PipelineResult(answer=_NO_CONTEXT_ANSWER, sources=[], chunks_used=0)

    # ------------------------------------------------------------------ #
    # 2. Build context block                                               #
    # ------------------------------------------------------------------ #
    context_parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        page_info = f"page {chunk.page_number}" if chunk.page_number else "unknown page"
        context_parts.append(
            f"[Source {i}: {chunk.filename}, {page_info}]\n{chunk.content}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # ------------------------------------------------------------------ #
    # 3. Call LLM                                                          #
    # ------------------------------------------------------------------ #
    answer = _call_llm(question=question, context=context)

    # ------------------------------------------------------------------ #
    # 4. Build source citations                                            #
    # ------------------------------------------------------------------ #
    sources = [
        {
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "filename": c.filename,
            "page_number": c.page_number,
            "chunk_index": c.chunk_index,
            "score": round(c.score, 4),
        }
        for c in chunks
    ]

    logger.info(
        "Pipeline complete — chunks_used=%d answer_len=%d",
        len(chunks), len(answer),
    )
    return PipelineResult(answer=answer, sources=sources, chunks_used=len(chunks))


def _call_llm(question: str, context: str) -> str:
    """Send the context + question to Gemini and return the answer string."""
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options={"api_version": "v1"},
    )
    user_message = build_prompt(context=context, question=question)

    try:
        response = client.models.generate_content(
            model=settings.llm_model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.0,
                max_output_tokens=1024,
            ),
        )
        answer = response.text or _NO_CONTEXT_ANSWER
        logger.info(
            "LLM response received (model=%s)",
            settings.llm_model,
        )
        return answer.strip()

    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        raise

