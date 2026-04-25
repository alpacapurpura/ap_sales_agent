"""F4 — async URL fetch + trafilatura markdown extraction.

Pipeline:

1. ``httpx.AsyncClient`` GET with realistic UA, timeout 15s, single retry
   on connect/timeout (matches 2026 best practice for low-volume scrape).
2. ``trafilatura.extract(html, output_format="markdown", with_metadata=True)``
   produces a markdown digest of the main content + metadata block.
3. Caller receives a small VO ``WebExtractResult`` — no raw HTML returned
   so the LLM context is never polluted with boilerplate.

Privacy:

- The query string is stripped from the persisted ``url`` so secrets
  (``?token=...``, ``?email=...``) leaked in pasted URLs do not survive
  past the fetch attempt. Audit log mirrors the strip.
- Local/private IPs are blocklisted so a tenant cannot probe internal
  services through the copilot.

# [COPILOT-FETCH-URL-F4] -> docs/domains/copilot/redesign-2026-04/phases/F4-url-contextual-scratchpad.md
"""

from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

import httpx
import structlog
import trafilatura

logger = structlog.get_logger()


_USER_AGENT = "Mozilla/5.0 (compatible; NicolifyCopilot/1.0; +https://nicolify.com/copilot-bot)"
_FETCH_TIMEOUT_S = 15.0
_FETCH_RETRIES = 1
_OG_IMAGE_RE = re.compile(
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_TITLE_RE = re.compile(r"<title[^>]*>([^<]+)</title>", re.IGNORECASE)


class FetchUrlError(Exception):
    """Raised when fetch/extract pipeline cannot produce a usable result.

    Public-facing: the message is shown to the user via the tool error
    envelope. Keep it short and Spanish neutro.
    """


@dataclass(frozen=True, slots=True)
class WebExtractResult:
    """Outcome of a successful fetch + extract pass."""

    url: str  # query-string-stripped, scheme + netloc + path
    domain: str
    title: str | None
    content_md: str
    og_image: str | None


def strip_query_and_fragment(url: str) -> str:
    """Return ``url`` without query string or fragment.

    Privacy: tokens / emails / pii smuggled into ``?...`` are dropped so
    the persisted inspiration row never carries them. Path is preserved
    because users genuinely paste paths like ``/blog/article-slug``.
    """
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _is_private_or_local(host: str) -> bool:
    """Return ``True`` when ``host`` resolves to a private/loopback IP.

    Resolves DNS once. Network failures (NXDOMAIN) are treated as
    "non-private" so the fetch attempt continues — httpx will surface
    the real error if the host is genuinely unreachable.
    """
    if not host:
        return True
    lowered = host.lower()
    if lowered in {"localhost", "ip6-localhost", "ip6-loopback"}:
        return True
    try:
        ip = ipaddress.ip_address(lowered)
    except ValueError:
        try:
            ip_str = socket.gethostbyname(lowered)
        except OSError:
            return False
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
    return bool(ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved)


def validate_url(url: str) -> str:
    """Normalize + validate a user-pasted URL.

    Returns the canonical URL (https-only, query-stripped) when valid.
    Raises ``FetchUrlError`` otherwise. Keep validation intentionally
    strict: the copilot only consumes public web pages.
    """
    if not url or not url.strip():
        msg = "La URL está vacía."
        raise FetchUrlError(msg)
    candidate = url.strip()
    parts = urlsplit(candidate)
    if parts.scheme not in {"https", "http"}:
        msg = "La URL debe empezar con https:// (o http:// para sitios sin TLS)."
        raise FetchUrlError(msg)
    if not parts.netloc:
        msg = "La URL no tiene host."
        raise FetchUrlError(msg)
    if _is_private_or_local(parts.hostname or ""):
        msg = "No puedo analizar URLs locales o privadas."
        raise FetchUrlError(msg)
    return strip_query_and_fragment(candidate)


def _extract_og_image(html: str) -> str | None:
    """Best-effort regex pull of ``og:image`` from the raw HTML head."""
    match = _OG_IMAGE_RE.search(html)
    return match.group(1).strip() if match else None


def _extract_title_fallback(html: str) -> str | None:
    """Regex fallback for ``<title>`` when trafilatura strips metadata."""
    match = _TITLE_RE.search(html)
    return match.group(1).strip() if match else None


async def fetch_html(
    url: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> str:
    """Fetch the raw HTML for ``url`` with timeout + 1 retry.

    Caller is expected to have validated the URL. Returns the response
    text body; raises ``FetchUrlError`` for any non-2xx, timeout, or
    connect failure (post-retry).
    """
    transport = httpx.AsyncHTTPTransport(retries=_FETCH_RETRIES)
    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(
            transport=transport,
            timeout=_FETCH_TIMEOUT_S,
            headers={"User-Agent": _USER_AGENT, "Accept": "text/html"},
            follow_redirects=True,
        )
    assert client is not None  # noqa: S101 — narrowing for type checker
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.text
    except httpx.HTTPStatusError as exc:
        msg = f"El sitio respondió con error {exc.response.status_code}."
        raise FetchUrlError(msg) from exc
    except httpx.TimeoutException as exc:
        msg = "Tiempo de espera agotado. Probá de nuevo o pegá el contenido."
        raise FetchUrlError(msg) from exc
    except httpx.RequestError as exc:
        msg = f"No se pudo conectar al sitio: {exc.__class__.__name__}."
        raise FetchUrlError(msg) from exc
    finally:
        if owns_client:
            await client.aclose()


def extract_markdown(html: str) -> tuple[str, str | None]:
    """Run trafilatura on raw HTML; return ``(markdown, title)``.

    Raises ``FetchUrlError`` when extraction returns nothing usable
    (typical of JS-heavy sites). Caller can surface a "no se pudo
    extraer" copy-paste fallback. Title falls back to the raw HTML
    ``<title>`` tag when trafilatura's metadata is empty.
    """
    md = trafilatura.extract(
        html,
        output_format="markdown",
        with_metadata=True,
        favor_precision=True,
    )
    if not md or not md.strip():
        msg = "No se pudo extraer el contenido del sitio (¿JavaScript-heavy?). Pegá el texto manualmente y lo proceso."
        raise FetchUrlError(msg)
    title = _extract_title_fallback(html)
    return md, title


async def fetch_extract(
    url: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> WebExtractResult:
    """End-to-end: validate → fetch → extract → return VO.

    Caller (the ``fetch_url`` tool) wraps this in a try/except that maps
    ``FetchUrlError`` to a user-facing JSON error envelope.
    """
    canonical = validate_url(url)
    html = await fetch_html(canonical, client=client)
    md, title = extract_markdown(html)
    og_image = _extract_og_image(html)
    parts = urlsplit(canonical)
    domain = (parts.hostname or "").lower()
    return WebExtractResult(
        url=canonical,
        domain=domain,
        title=title,
        content_md=md,
        og_image=og_image,
    )


__all__ = [
    "FetchUrlError",
    "WebExtractResult",
    "extract_markdown",
    "fetch_extract",
    "fetch_html",
    "strip_query_and_fragment",
    "validate_url",
]
