"""Friendly redirect template when user requests web-only tool from Telegram.

D-PI5-025 — UX template, NO error técnico. Spanish neutro tuteo
(rule ``spanish-text.md``).
"""

from __future__ import annotations

from typing import Final

from luana_core_platform.core.config import settings

# Spanish neutro tuteo. Anti-pattern A12 (research §7).
TELEGRAM_TOOL_UNAVAILABLE_TEMPLATE: Final[str] = (
    "Ese ajuste requiere el editor web. "
    "Aquí tienes el link directo: {url}\n\n"
    "¿Quieres que te lo recuerde más tarde o prefieres abrirlo ahora?"
)


def build_redirect_url(tenant_id: str, target_path: str) -> str:
    """Construye URL absoluta hacia FE app.

    Ejemplo: ``("abc-123", "/landing")`` → ``"https://app.nicolify.com/abc-123/landing"``
    """
    base = settings.FRONTEND_URL.rstrip("/")
    path = target_path if target_path.startswith("/") else f"/{target_path}"
    return f"{base}/{tenant_id}{path}"


def render_unavailable_response(tenant_id: str, target_path: str) -> str:
    """Render full Telegram-friendly redirect message."""
    url = build_redirect_url(tenant_id, target_path)
    return TELEGRAM_TOOL_UNAVAILABLE_TEMPLATE.format(url=url)
