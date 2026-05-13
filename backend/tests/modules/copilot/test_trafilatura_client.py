"""Tests for ``trafilatura_client`` — F4 url fetch + extract."""

from __future__ import annotations

import httpx
import pytest

from luana_core_copilot.infrastructure.web import trafilatura_client as tc

# ── Validation ───────────────────────────────────────────────────────────


class TestValidateUrl:
    def test_https_passes(self) -> None:
        assert tc.validate_url("https://example.com/path") == "https://example.com/path"

    def test_http_passes(self) -> None:
        assert tc.validate_url("http://example.com").startswith("http://")

    def test_strips_query_string(self) -> None:
        out = tc.validate_url("https://example.com/p?token=abc&user=me")
        assert "?" not in out
        assert "token" not in out

    def test_strips_fragment(self) -> None:
        out = tc.validate_url("https://example.com/p#section")
        assert "#" not in out

    def test_rejects_empty(self) -> None:
        with pytest.raises(tc.FetchUrlError):
            tc.validate_url("")

    def test_rejects_non_http_scheme(self) -> None:
        with pytest.raises(tc.FetchUrlError):
            tc.validate_url("ftp://example.com")

    def test_rejects_localhost(self) -> None:
        with pytest.raises(tc.FetchUrlError):
            tc.validate_url("http://localhost:3000/api")

    def test_rejects_loopback_ip(self) -> None:
        with pytest.raises(tc.FetchUrlError):
            tc.validate_url("http://127.0.0.1:8000")

    def test_rejects_private_ip(self) -> None:
        with pytest.raises(tc.FetchUrlError):
            tc.validate_url("http://192.168.1.1")


# ── strip_query_and_fragment ─────────────────────────────────────────────


class TestStripQueryFragment:
    def test_preserves_path(self) -> None:
        assert tc.strip_query_and_fragment("https://x.com/blog/post?utm=1#h") == "https://x.com/blog/post"

    def test_no_query_no_change(self) -> None:
        assert tc.strip_query_and_fragment("https://x.com/y") == "https://x.com/y"


# ── extract_markdown ─────────────────────────────────────────────────────


_FIXTURE_HTML = """<!DOCTYPE html>
<html>
<head>
<title>Mujer Coraje · Programa Despertar</title>
<meta property="og:image" content="https://cdn.example.com/og.jpg">
</head>
<body>
<header><nav>menú</nav></header>
<main>
<article>
<h1>Programa Despertar</h1>
<p>Para mujeres que quieren reinventarse a los 40. Acompañamiento de
12 semanas con grupo cerrado.</p>
<h2>Testimonios</h2>
<blockquote>"Cambió mi vida en 8 semanas." — Lucía, 42</blockquote>
<h2>Inversión</h2>
<p>USD 1,200 — pagos en 3 cuotas.</p>
</article>
</main>
<footer>copyright</footer>
</body>
</html>"""


class TestExtractMarkdown:
    def test_returns_markdown_with_title(self) -> None:
        md, title = tc.extract_markdown(_FIXTURE_HTML)
        assert md
        assert "Despertar" in md
        assert title and "Mujer Coraje" in title

    def test_raises_on_empty_html(self) -> None:
        with pytest.raises(tc.FetchUrlError):
            tc.extract_markdown("<html><body></body></html>")


# ── og_image ─────────────────────────────────────────────────────────────


class TestOgImage:
    def test_extracts_og_image(self) -> None:
        # Indirectly via fetch_extract path is async; test the regex directly.
        from luana_core_copilot.infrastructure.web.trafilatura_client import (
            _extract_og_image,
        )

        assert _extract_og_image(_FIXTURE_HTML) == "https://cdn.example.com/og.jpg"


# ── fetch_extract end-to-end (mocked transport) ─────────────────────────


class TestFetchExtractMocked:
    @pytest.mark.asyncio
    async def test_full_pipeline_success(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                text=_FIXTURE_HTML,
                headers={"content-type": "text/html"},
            )

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            result = await tc.fetch_extract(
                "https://mujercoraje.example.com/programa",
                client=client,
            )
        assert result.url == "https://mujercoraje.example.com/programa"
        assert result.domain == "mujercoraje.example.com"
        assert "Despertar" in result.content_md
        assert result.og_image == "https://cdn.example.com/og.jpg"

    @pytest.mark.asyncio
    async def test_http_error_raises_fetch_error(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503)

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            with pytest.raises(tc.FetchUrlError):
                await tc.fetch_extract("https://example.com/x", client=client)

    @pytest.mark.asyncio
    async def test_query_stripped_in_canonical(self) -> None:
        captured: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            captured.append(str(request.url))
            return httpx.Response(200, text=_FIXTURE_HTML)

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            result = await tc.fetch_extract(
                "https://example.com/p?token=secret",
                client=client,
            )
        # The persisted url has no query.
        assert "token" not in result.url
        # And the actual GET also went without the query.
        assert all("token" not in u for u in captured)
