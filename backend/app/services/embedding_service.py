"""
Embedding service — generates vector embeddings for text using OpenAI.

Batches chunks to stay within the API's per-request token limit.
Retries transient errors with exponential back-off.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_BATCH_SIZE = 100          # chunks per API call (OpenAI limit is 2048 inputs)
_MAX_RETRIES = 3
_BACKOFF_BASE = 2.0        # seconds


def _get_client():
    """Return a cached OpenAI client (lazy init)."""
    from openai import OpenAI
    return OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return a list of embedding vectors, one per input text.

    Args:
        texts: List of strings to embed.

    Returns:
        List of float vectors in the same order as *texts*.

    Raises:
        RuntimeError: If the API call fails after all retries.
    """
    if not texts:
        return []

    client = _get_client()
    all_embeddings: list[list[float]] = []

    for batch_start in range(0, len(texts), _BATCH_SIZE):
        batch = texts[batch_start : batch_start + _BATCH_SIZE]
        embeddings = _embed_batch_with_retry(client, batch)
        all_embeddings.extend(embeddings)
        logger.debug(
            "Embedded batch %d-%d / %d",
            batch_start, batch_start + len(batch), len(texts),
        )

    return all_embeddings


def _embed_batch_with_retry(client: Any, texts: list[str]) -> list[list[float]]:
    """Embed a single batch with retry logic."""
    last_exc: Exception | None = None

    for attempt in range(_MAX_RETRIES):
        try:
            response = client.embeddings.create(
                model=settings.embedding_model,
                input=texts,
            )
            # Sort by index to guarantee order matches input
            return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
        except Exception as exc:
            last_exc = exc
            wait = _BACKOFF_BASE ** attempt
            logger.warning(
                "Embedding attempt %d/%d failed: %s — retrying in %.1fs",
                attempt + 1, _MAX_RETRIES, exc, wait,
            )
            time.sleep(wait)

    raise RuntimeError(
        f"Embedding API failed after {_MAX_RETRIES} attempts: {last_exc}"
    )


def embed_query(text: str) -> list[float]:
    """Embed a single query string. Returns one vector."""
    results = embed_texts([text])
    if not results:
        raise RuntimeError("Embedding API returned empty result for query")
    return results[0]
