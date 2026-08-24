"""
PDF loader using PyMuPDF (fitz).

Returns a list of (page_number, text) tuples — one entry per page.
The caller (chunker) decides how to split across pages.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PageText:
    page_number: int   # 1-based
    text: str


def load_pdf(file_path: str | Path) -> list[PageText]:
    """Extract text from every page of a PDF.

    Returns a list of PageText objects (one per page, 1-indexed).
    Empty pages are included so chunk_index ↔ page_number mapping stays consistent.
    """
    import fitz  # PyMuPDF — imported lazily so the module loads even without it

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    pages: list[PageText] = []
    try:
        with fitz.open(str(path)) as doc:
            logger.info("Loading PDF: %s (%d pages)", path.name, len(doc))
            for i, page in enumerate(doc, start=1):
                text = page.get_text("text")  # plain text extraction
                pages.append(PageText(page_number=i, text=text or ""))
    except Exception as exc:
        logger.error("Failed to load PDF %s: %s", path, exc)
        raise

    logger.info("Extracted %d pages from %s", len(pages), path.name)
    return pages
