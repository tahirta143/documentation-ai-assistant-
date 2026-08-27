"""
URL loader — scrapes web pages and extracts clean text content.
"""

from __future__ import annotations

import logging
import re
from bs4 import BeautifulSoup
import httpx

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36 DocumentationAssistant/1.0"
    )
}


def load_url(url: str, timeout: float = 15.0) -> tuple[str, str]:
    """Fetch a web page, parse HTML, and return (page_title, clean_text_content).

    Args:
        url: The web URL to scrape.
        timeout: Request timeout in seconds.

    Returns:
        tuple (title, cleaned_text)
    """
    logger.info("Fetching URL content from: %s", url)
    with httpx.Client(follow_redirects=True, timeout=timeout, headers=HEADERS) as client:
        response = client.get(url)
        response.raise_for_status()
        html = response.text

    soup = BeautifulSoup(html, "html.parser")

    # Extract title
    title = soup.title.string.strip() if (soup.title and soup.title.string) else url

    # Remove unwanted tags
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "iframe"]):
        tag.decompose()

    # Prioritize main or article if present
    main_content = soup.find("main") or soup.find("article") or soup.find("body") or soup
    raw_text = main_content.get_text(separator="\n")

    # Normalize whitespace
    lines = [line.strip() for line in raw_text.splitlines()]
    text = "\n".join(line for line in lines if line)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return title, text
