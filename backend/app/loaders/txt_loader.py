"""
Plain-text loader.

Reads a .txt file with automatic encoding detection.
Tries UTF-8 first, then latin-1 as a safe fallback.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_ENCODINGS_TO_TRY = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]


def load_txt(file_path: str | Path) -> str:
    """Read a plain text file and return its contents as a string."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {path}")

    for encoding in _ENCODINGS_TO_TRY:
        try:
            text = path.read_text(encoding=encoding)
            logger.info(
                "Loaded TXT: %s (%d chars, encoding=%s)",
                path.name, len(text), encoding,
            )
            return text
        except UnicodeDecodeError:
            logger.debug("Encoding %s failed for %s, trying next", encoding, path.name)
            continue

    # Last resort: replace undecodable bytes
    text = path.read_text(encoding="utf-8", errors="replace")
    logger.warning("Loaded %s with replacement characters (unknown encoding)", path.name)
    return text
