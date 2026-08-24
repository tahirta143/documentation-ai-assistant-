"""
Text cleaning utilities.

Applies a series of normalisation steps to raw extracted text:
  - Remove null bytes and other control characters
  - Collapse excessive whitespace / blank lines
  - Strip leading/trailing whitespace per line
  - Normalise unicode ligatures and fancy quotes
"""

import re
import unicodedata


# Characters to remove entirely (non-printable control chars except \n \t)
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Three or more consecutive blank lines → two blank lines
_EXCESS_BLANK_LINES_RE = re.compile(r"\n{3,}")

# Multiple spaces / tabs on a single line → single space
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")

# Unicode ligatures and fancy punctuation map
_UNICODE_MAP = str.maketrans(
    {
        "\u2018": "'",   # left single quotation mark
        "\u2019": "'",   # right single quotation mark
        "\u201c": '"',   # left double quotation mark
        "\u201d": '"',   # right double quotation mark
        "\u2013": "-",   # en dash
        "\u2014": "--",  # em dash
        "\u2026": "...", # ellipsis
        "\ufb01": "fi",  # fi ligature
        "\ufb02": "fl",  # fl ligature
        "\u00a0": " ",   # non-breaking space
    }
)


def clean_text(text: str) -> str:
    """Return a normalised version of *text* suitable for chunking / embedding.

    Steps applied (in order):
    1. NFKC unicode normalisation (handles composed/decomposed forms, ligatures)
    2. Replace fancy punctuation with ASCII equivalents
    3. Strip control characters
    4. Strip trailing whitespace from each line
    5. Collapse consecutive blank lines
    6. Collapse multiple spaces on a single line
    7. Final strip
    """
    if not text:
        return ""

    # 1. Unicode normalisation
    text = unicodedata.normalize("NFKC", text)

    # 2. Fancy punctuation → ASCII
    text = text.translate(_UNICODE_MAP)

    # 3. Remove control characters
    text = _CONTROL_CHARS_RE.sub("", text)

    # 4. Strip trailing whitespace per line
    lines = [line.rstrip() for line in text.splitlines()]
    text = "\n".join(lines)

    # 5. Collapse excess blank lines
    text = _EXCESS_BLANK_LINES_RE.sub("\n\n", text)

    # 6. Collapse multiple spaces
    text = _MULTI_SPACE_RE.sub(" ", text)

    # 7. Final strip
    return text.strip()
