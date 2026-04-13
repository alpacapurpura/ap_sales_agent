"""Pure helpers for URL normalization and text tokenization.

Used by OfferDetectionService to match ads <-> offers.
No framework or DB imports — plain Python only.
"""

import re
from urllib.parse import urlsplit

SPANISH_STOPWORDS: frozenset[str] = frozenset(
    {
        "de",
        "la",
        "el",
        "los",
        "las",
        "un",
        "una",
        "unas",
        "unos",
        "para",
        "con",
        "por",
        "en",
        "y",
        "o",
        "del",
        "al",
        "a",
        "e",
        "es",
        "se",
        "su",
        "sus",
        "me",
        "mi",
        "te",
        "tu",
        "lo",
        "le",
        "que",
        "como",
        "sin",
    },
)

_PUNCT_RE = re.compile(r"[\W_]+", flags=re.UNICODE)


def normalize_url(url: str | None) -> str:
    """Normalize a URL for fuzzy matching.

    - lowercase
    - strip scheme (http/https)
    - strip leading www.
    - strip query string
    - strip trailing slash
    - keep the hostname + path
    """
    if not url:
        return ""
    raw = url.strip()
    if not raw:
        return ""

    # Ensure the parser has a scheme so hostname is detected.
    if "://" not in raw:
        raw = "http://" + raw

    parts = urlsplit(raw)
    host = (parts.hostname or "").lower()
    host = host.removeprefix("www.")
    path = (parts.path or "").rstrip("/")
    normalized = f"{host}{path}".lower()
    return normalized


def urls_match(url_a: str | None, url_b: str | None) -> bool:
    """Return True if two URLs (after normalization) share the same path prefix.

    Match is symmetric: one URL may contain the other. This allows a
    specific ad landing page to match a shorter offer URL and vice versa.
    """
    a = normalize_url(url_a)
    b = normalize_url(url_b)
    if not a or not b:
        return False
    if a == b:
        return True
    return a in b or b in a


def tokenize_es(text: str | None) -> set[str]:
    """Tokenize Spanish text for Jaccard similarity."""
    if not text:
        return set()
    lowered = text.lower()
    # Replace punctuation with spaces.
    cleaned = _PUNCT_RE.sub(" ", lowered)
    tokens = {tok for tok in cleaned.split() if len(tok) >= 3 and tok not in SPANISH_STOPWORDS}
    return tokens


def jaccard_similarity(a: set[str], b: set[str]) -> float:
    """Jaccard similarity in [0.0, 1.0]."""
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    if union == 0:
        return 0.0
    return intersection / union
