"""ARQ worker job: ``process_copilot_telegram_turn``.

D-PI5-026 NON-BLOCKING contract. Webhook handler enqueues a sanitized
payload < 200ms; this worker processes LLM async + sends response via
bot. Graceful degradation: log + drop after retry exhausted (NEVER
raise to ARQ to avoid infinite retry).
"""

from __future__ import annotations

from typing import Any

import structlog

from src.modules.copilot.api._dependencies import copilot_async_session_factory
from src.modules.copilot.application.services.telegram_link_service import (
    consume_link_token,
    resolve_chat_id_to_tenant_user,
    touch_last_seen,
)
from src.modules.copilot.infrastructure.channels.telegram_bot import (
    CopilotTelegramBot,
)

_LOGGER = structlog.get_logger(__name__)


# Onboarding response when bot receives DM without active link
_UNLINKED_CTA_TEMPLATE = (
    "Hola. Soy el copilot de Nicolify.\n\n"
    "Para usarme, conéctate primero desde tu cuenta:\n"
    "{onboarding_url}\n\n"
    "El proceso toma 30 segundos."
)

_LINK_BOUND_RESPONSE = (
    "Listo. Ya puedes usar el copilot desde Telegram. "
    "Pregúntame cualquier cosa de tu negocio o déjame encargos para procesar."
)

_LINK_INVALID_RESPONSE = (
    "Ese enlace ya no es válido (expiró o fue usado).\n\nGenera uno nuevo desde tu cuenta:\n{onboarding_url}"
)


async def process_copilot_telegram_turn(
    ctx: dict[str, Any],
    payload: dict[str, Any],
) -> None:
    """Process inbound Telegram message.

    payload schema (sanitized at handler):
        - update_id: int
        - chat_id: str (numeric as str)
        - message_id: int
        - text: str
        - username: str | None (mutable display)
        - received_at: ISO datetime str

    Steps:
    1. Resolve chat_id → channel_link → (tenant_id, user_id, role) | None
    2. If unlinked AND text starts with "/start TOKEN":
        - Validate token (hash + TTL + unused) → bind chat_id → reply success
       Else if unlinked:
        - send unlinked CTA response with onboarding URL
       Else (linked):
        - Update last_seen_at
        - Invoke orchestrator with channel='telegram', tenant_id, user_id
          (orchestrator hookup in Sprint 2 PR-2 — for MVP foundation,
          send placeholder reply to confirm reception)
    3. structlog with try/except — never raise to ARQ
    """
    chat_id: str = payload.get("chat_id", "")
    text: str = payload.get("text", "") or ""
    username: str | None = payload.get("username")

    if not chat_id:
        _LOGGER.warning("copilot_telegram_worker_missing_chat_id")
        return

    bot = CopilotTelegramBot()

    try:
        async with copilot_async_session_factory() as db:
            link = await resolve_chat_id_to_tenant_user(db, channel_user_id=chat_id, channel_type="telegram")

            # ── /start TOKEN flow (onboarding) ────────────────────────
            if text.startswith("/start "):
                plaintext_token = text.removeprefix("/start ").strip()
                if plaintext_token:
                    new_link = await consume_link_token(
                        db,
                        plaintext_token=plaintext_token,
                        channel_user_id=chat_id,
                        channel_username=username,
                    )
                    if new_link is not None:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=_LINK_BOUND_RESPONSE,
                        )
                        return
                # invalid token
                onboarding_url = _build_onboarding_url()
                await bot.send_message(
                    chat_id=chat_id,
                    text=_LINK_INVALID_RESPONSE.format(onboarding_url=onboarding_url),
                )
                return

            # ── Bare /start (no token) → CTA ─────────────────────────
            if text.strip() == "/start":
                onboarding_url = _build_onboarding_url()
                await bot.send_message(
                    chat_id=chat_id,
                    text=_UNLINKED_CTA_TEMPLATE.format(onboarding_url=onboarding_url),
                )
                return

            # ── Unlinked DM → CTA ─────────────────────────────────────
            if link is None:
                onboarding_url = _build_onboarding_url()
                _LOGGER.info(
                    "copilot_telegram_unlinked_message_received",
                    chat_id_prefix=_mask_chat_id(chat_id),
                )
                await bot.send_message(
                    chat_id=chat_id,
                    text=_UNLINKED_CTA_TEMPLATE.format(onboarding_url=onboarding_url),
                )
                return

            # ── Linked DM → invoke orchestrator (S2 PR-2 hookup) ──────
            await touch_last_seen(db, link_id=link.id)

            # MVP placeholder response (S1 foundation only).
            # S2 PR-2 wires orchestrator with channel='telegram' +
            # TELEGRAM_CONTEXT_WINDOW_CONFIG memory.
            _LOGGER.info(
                "copilot_telegram_linked_message_received",
                tenant_id=str(link.tenant_id),
                user_id=str(link.user_id),
                chat_id_prefix=_mask_chat_id(chat_id),
                text_len_chars=len(text),
            )
            await bot.send_message(
                chat_id=chat_id,
                text=(
                    "Recibí tu mensaje. La integración completa del "
                    "copilot conversacional vía Telegram llega en el "
                    "próximo sprint (PI-5 S2). Por ahora confirmo que "
                    "tu Telegram está conectado correctamente."
                ),
            )

    except Exception as exc:
        # Graceful degradation — never raise to ARQ
        _LOGGER.exception(
            "copilot_telegram_worker_unhandled_error",
            chat_id_prefix=_mask_chat_id(chat_id),
            error=str(exc),
        )


def _build_onboarding_url() -> str:
    """Build CTA URL pointing to FE onboarding page (general settings).

    Tenant-aware URL not possible here (we don't know which tenant
    the unauthenticated chat belongs to). User must auth in-app first
    to see their Telegram settings.
    """
    from src.core.config import settings

    base = settings.FRONTEND_URL.rstrip("/")
    return f"{base}/settings/copilot/telegram"


def _mask_chat_id(chat_id: str) -> str:
    """First 5 chars + '***' for log redaction (anti-pattern A3)."""
    if len(chat_id) <= 5:
        return "***"
    return f"{chat_id[:5]}***"


__all__ = ["process_copilot_telegram_turn"]
