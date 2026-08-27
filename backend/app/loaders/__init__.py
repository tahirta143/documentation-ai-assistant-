"""
Loader factory.

Usage:
    from app.loaders import load_document, LoadedDocument

    doc = load_document("path/to/file.pdf", "pdf")
    # doc.pages  → list of (page_number, text) for PDFs
    # doc.full_text → concatenated clean string
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LoadedDocument:
    """Unified output from any loader."""
    file_type: str
    # For PDFs: one entry per page. For MD/TXT/URL: a single entry with page_number=1.
    pages: list[tuple[int, str]] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """All pages concatenated with double newline separation."""
        return "\n\n".join(text for _, text in self.pages if text.strip())


def load_document(file_path: str | Path, file_type: str) -> LoadedDocument:
    """Dispatch to the right loader based on *file_type* and return a LoadedDocument.

    Args:
        file_path: Absolute or relative path to the file on disk (or URL).
        file_type: One of 'pdf', 'md', 'txt', 'url'.

    Returns:
        LoadedDocument with .pages populated.

    Raises:
        ValueError: For unsupported file types.
        FileNotFoundError: If the local file doesn't exist.
    """
    ext = file_type.lower().lstrip(".")

    if ext == "pdf":
        from app.loaders.pdf_loader import load_pdf
        from app.utils.text_cleaner import clean_text

        raw_pages = load_pdf(file_path)
        pages = [(p.page_number, clean_text(p.text)) for p in raw_pages]
        return LoadedDocument(file_type="pdf", pages=pages)

    elif ext in ("md", "markdown"):
        from app.loaders.markdown_loader import load_markdown
        from app.utils.text_cleaner import clean_text

        text = clean_text(load_markdown(file_path))
        return LoadedDocument(file_type="md", pages=[(1, text)])

    elif ext == "txt":
        from app.loaders.txt_loader import load_txt
        from app.utils.text_cleaner import clean_text

        text = clean_text(load_txt(file_path))
        return LoadedDocument(file_type="txt", pages=[(1, text)])

    elif ext == "url":
        from app.loaders.url_loader import load_url
        from app.utils.text_cleaner import clean_text

        # If file_path is stored file with URL contents or direct url string
        url_str = str(file_path)
        if Path(file_path).exists():
            # If path points to a saved file containing the scraped markdown/text
            text = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        else:
            _, text = load_url(url_str)
        cleaned = clean_text(text)
        return LoadedDocument(file_type="url", pages=[(1, cleaned)])

    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: pdf, md, txt, url"
        )
