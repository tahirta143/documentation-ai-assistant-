"""
Markdown loader.

Strips Markdown syntax and returns clean plain text.
Strategy: parse Markdown → HTML via markdown-it-py, then
strip HTML tags with BeautifulSoup.  Falls back to raw text
if either library is unavailable.
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Patterns for a lightweight fallback if markdown-it-py isn't installed
_HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
_CODE_FENCE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_BOLD_ITALIC_RE = re.compile(r"\*{1,3}([^*]+)\*{1,3}")
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]+\)")
_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_markdown_fallback(text: str) -> str:
    """Lightweight regex-based markdown stripper (no extra deps)."""
    text = _IMAGE_RE.sub("", text)          # remove images
    text = _LINK_RE.sub(r"\1", text)        # keep link text
    text = _CODE_FENCE_RE.sub("", text)     # remove code blocks
    text = _INLINE_CODE_RE.sub(r"\1", text) # keep inline code content
    text = _BOLD_ITALIC_RE.sub(r"\1", text) # keep bold/italic content
    text = _HEADING_RE.sub("", text)        # remove heading markers
    text = _HTML_TAG_RE.sub("", text)       # strip any embedded HTML
    return text


def load_markdown(file_path: str | Path) -> str:
    """Read a Markdown file and return plain text.

    Tries markdown-it-py + BeautifulSoup for clean extraction.
    Falls back to a lightweight regex stripper if those aren't available.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {path}")

    raw = path.read_text(encoding="utf-8", errors="replace")
    logger.info("Loading Markdown: %s (%d chars)", path.name, len(raw))

    try:
        from markdown_it import MarkdownIt  # type: ignore
        from bs4 import BeautifulSoup

        md = MarkdownIt()
        html = md.render(raw)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n")
        logger.info("Extracted markdown via markdown-it-py + BeautifulSoup")
        return text

    except ImportError:
        logger.debug("markdown-it-py not available, using regex fallback")
        return _strip_markdown_fallback(raw)
