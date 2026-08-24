"""
Loader factory.

Usage:
    from app.loaders import get_loader, LoadedDocument

    doc = get_loader("pdf").load("path/to/file.pdf")
    # doc.pages  → list of (page_number, text) for PDFs
    # doc.text   → single concatenated string for MD/TXT
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
    # For PDFs: one entry per page.  For MD/TXT: a single entry with page_number=1.
    pages: list[tuple[int, str]] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """All pages concatenated with double newline separation."""
        return "\n\n".join(text for _, text in self.pages if text.strip())


def load_document(file_path: str | Path, file_type: str) -> LoadedDocument:
    """Dispatch to the right loader based on *file_type* and return a LoadedDocument.

    Args:
        file_path: Absolute or relative path to the file on disk.
        file_type: One of 'pdf', 'md', 'txt'.

    Returns:
        LoadedDocument with .pages populated.

    Raises:
        ValueError: For unsupported file types.
        FileNotFoundError: If the file doesn't exist.
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

    else:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: pdf, md, txt"
        )
