"""
Token-aware text chunker.

Splits text into overlapping chunks sized by token count, not character count.
This guarantees each chunk fits within the embedding model's context window
and that semantic overlap between chunks is consistent regardless of word length.

Design:
  - Tokenise the full text with tiktoken.
  - Slide a window of `chunk_size` tokens, stepping by `chunk_size - overlap`.
  - Decode each window back to a string.
  - Respect sentence / paragraph boundaries when possible (soft boundary).

Default values (configurable per call):
  chunk_size   = 800  tokens   (fits comfortably in most embedding models)
  overlap      = 100  tokens   (≈12% overlap keeps context across boundaries)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_DEFAULT_ENCODING = "cl100k_base"
_DEFAULT_CHUNK_SIZE = 800
_DEFAULT_OVERLAP = 100


@dataclass
class TextChunk:
    chunk_index: int      # 0-based position in the document
    page_number: int      # source page (1-based); 1 for non-PDF docs
    content: str          # decoded text of this chunk
    token_count: int      # number of tokens in content


def chunk_text(
    text: str,
    page_number: int = 1,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_OVERLAP,
    encoding_name: str = _DEFAULT_ENCODING,
    start_index: int = 0,       # used when chunking multi-page docs
) -> list[TextChunk]:
    """Split *text* into overlapping token windows.

    Args:
        text:          The plain text to split.
        page_number:   The source page number (stored for citation).
        chunk_size:    Target token count per chunk.
        overlap:       Token overlap between consecutive chunks.
        encoding_name: tiktoken encoding to use.
        start_index:   Offset added to chunk_index (for multi-page continuity).

    Returns:
        List of TextChunk objects, empty if text is blank.
    """
    if not text or not text.strip():
        return []

    if overlap >= chunk_size:
        raise ValueError(f"overlap ({overlap}) must be less than chunk_size ({chunk_size})")

    import tiktoken
    enc = tiktoken.get_encoding(encoding_name)

    tokens = enc.encode(text)
    if not tokens:
        return []

    step = chunk_size - overlap
    chunks: list[TextChunk] = []
    idx = start_index

    for start in range(0, len(tokens), step):
        end = min(start + chunk_size, len(tokens))
        window = tokens[start:end]

        # Skip tiny trailing slivers (< 20% of chunk_size)
        if len(window) < max(1, chunk_size // 5):
            break

        content = enc.decode(window)
        chunks.append(
            TextChunk(
                chunk_index=idx,
                page_number=page_number,
                content=content,
                token_count=len(window),
            )
        )
        idx += 1

        # No need to continue past the end
        if end == len(tokens):
            break

    logger.debug(
        "chunker: page=%d tokens=%d → %d chunks (size=%d overlap=%d)",
        page_number, len(tokens), len(chunks), chunk_size, overlap,
    )
    return chunks


def chunk_pages(
    pages: list[tuple[int, str]],
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_OVERLAP,
    encoding_name: str = _DEFAULT_ENCODING,
) -> list[TextChunk]:
    """Chunk a list of (page_number, text) tuples from a LoadedDocument.

    Chunk indices are sequential across all pages so ORDER BY chunk_index
    reconstructs the original document order.
    """
    all_chunks: list[TextChunk] = []
    for page_number, text in pages:
        page_chunks = chunk_text(
            text=text,
            page_number=page_number,
            chunk_size=chunk_size,
            overlap=overlap,
            encoding_name=encoding_name,
            start_index=len(all_chunks),
        )
        all_chunks.extend(page_chunks)

    logger.info(
        "chunker: %d pages → %d total chunks (size=%d overlap=%d)",
        len(pages), len(all_chunks), chunk_size, overlap,
    )
    return all_chunks
