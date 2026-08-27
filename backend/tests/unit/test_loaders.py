"""
Unit tests for document loaders (Markdown, TXT, and URL loader logic).
"""

from unittest.mock import MagicMock, patch

from app.loaders import load_document
from app.loaders.markdown_loader import load_markdown
from app.loaders.txt_loader import load_txt


def test_txt_loader(tmp_path):
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("This is plain text content.", encoding="utf-8")

    doc = load_document(txt_file, "txt")
    assert doc.file_type == "txt"
    assert "This is plain text content." in doc.full_text


def test_markdown_loader(tmp_path):
    md_file = tmp_path / "sample.md"
    md_file.write_text("# Heading\n\nThis is **markdown** content.", encoding="utf-8")

    doc = load_document(md_file, "md")
    assert doc.file_type == "md"
    assert "Heading" in doc.full_text
    assert "markdown" in doc.full_text


def test_url_loader_mock(tmp_path):
    mock_html = """
    <html>
      <head><title>FastAPI Documentation</title></head>
      <body>
        <nav><a href="/">Home</a></nav>
        <main>
          <h1>FastAPI Framework</h1>
          <p>FastAPI is a modern, fast web framework for building APIs with Python.</p>
        </main>
        <footer>Footer noise to ignore</footer>
      </body>
    </html>
    """
    with patch("httpx.Client") as mock_client:
        mock_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_instance.get.return_value = mock_response
        mock_instance.__enter__.return_value = mock_instance
        mock_client.return_value = mock_instance

        from app.loaders.url_loader import load_url

        title, text = load_url("https://example.com/fastapi")
        assert title == "FastAPI Documentation"
        assert "FastAPI Framework" in text
        assert "Footer noise" not in text
        assert "Home" not in text
