"""
Token counting utility using tiktoken.

Uses the cl100k_base encoding (shared by GPT-4, text-embedding-3-small/large)
which is the most common encoding for modern OpenAI models.
"""

import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# Default encoding — works for GPT-4, text-embedding-3-small, gpt-3.5-turbo
_DEFAULT_ENCODING = "cl100k_base"


@lru_cache(maxsize=4)
def _get_encoder(encoding_name: str):
    """Cache encoder instances (initialisation is expensive)."""
    import tiktoken
    return tiktoken.get_encoding(encoding_name)


def count_tokens(text: str, encoding: str = _DEFAULT_ENCODING) -> int:
    """Return the number of tokens in *text* for the given tiktoken encoding."""
    if not text:
        return 0
    try:
        enc = _get_encoder(encoding)
        return len(enc.encode(text))
    except Exception as exc:
        # Fall back to a rough word-count estimate if tiktoken fails
        logger.warning("tiktoken count failed (%s), using word estimate", exc)
        return len(text.split())


def truncate_to_tokens(
    text: str,
    max_tokens: int,
    encoding: str = _DEFAULT_ENCODING,
) -> str:
    """Truncate *text* so it contains at most *max_tokens* tokens."""
    if not text:
        return ""
    try:
        enc = _get_encoder(encoding)
        tokens = enc.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return enc.decode(tokens[:max_tokens])
    except Exception as exc:
        logger.warning("tiktoken truncate failed (%s), using char estimate", exc)
        # Rough fallback: ~4 chars per token
        return text[: max_tokens * 4]
