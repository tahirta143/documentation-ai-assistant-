"""
Unit tests for text chunker.
"""

from app.rag.chunker import chunk_pages, chunk_text


def test_chunk_text_basic():
    text = "Hello world! This is a simple test document for the chunker."
    chunks = chunk_text(text, chunk_size=50, overlap=10)

    assert len(chunks) >= 1
    assert all(c.content for c in chunks)
    assert chunks[0].chunk_index == 0


def test_chunk_pages():
    pages = [
        (1, "Page one introduction content about documentation."),
        (2, "Page two detailed content with architecture and design."),
    ]
    chunks = chunk_pages(pages, chunk_size=50, overlap=10)

    assert len(chunks) >= 2
    assert any(c.page_number == 1 for c in chunks)
    assert any(c.page_number == 2 for c in chunks)
