"""Unit tests for telegram_redirect template (PI-5 PR-1).

Covers:
- URL building with FRONTEND_URL fallback
- Template substitution
- Spanish neutro tuteo (no voseo)
"""

from __future__ import annotations

from src.modules.copilot.application.tools.telegram_redirect import (
    TELEGRAM_TOOL_UNAVAILABLE_TEMPLATE,
    build_redirect_url,
    render_unavailable_response,
)


def test_build_redirect_url_with_leading_slash() -> None:
    url = build_redirect_url("tenant-abc", "/landing")
    assert url.endswith("/tenant-abc/landing")


def test_build_redirect_url_without_leading_slash() -> None:
    url = build_redirect_url("tenant-abc", "landing")
    assert url.endswith("/tenant-abc/landing")


def test_render_unavailable_response_substitutes_url() -> None:
    response = render_unavailable_response("tenant-abc", "/offer/section/123")
    assert "/tenant-abc/offer/section/123" in response
    assert "editor web" in response  # Spanish copy preserved


def test_template_uses_spanish_neutro_tuteo() -> None:
    """Template MUST use tuteo, NOT voseo (rule spanish-text.md)."""
    text = TELEGRAM_TOOL_UNAVAILABLE_TEMPLATE.lower()
    forbidden_voseo = ["tenés", "querés", "podés", "andá", "fijate", "elegí"]
    for term in forbidden_voseo:
        assert term not in text, f"Template contains voseo '{term}' — must use tuteo (LatAm neutral)"
    # Tuteo markers expected
    assert "tienes" in text or "quieres" in text or "prefieres" in text
