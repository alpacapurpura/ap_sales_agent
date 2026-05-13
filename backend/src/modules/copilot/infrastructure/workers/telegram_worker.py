"""ARQ worker job: ``process_copilot_telegram_turn``.

D-PI5-026 NON-BLOCKING contract. Webhook handler enqueues a sanitized
payload < 200ms; this worker processes LLM async + sends response via
bot. Graceful degradation: log + drop after retry exhausted (NEVER
raise to ARQ to avoid infinite retry).
"""

from __future__ import annotations

import asyncio
from typing import Any

import structlog
from luana_core_channels.format_for_channel import (
    format_for_channel_impl,
)
from luana_core_copilot.api._dependencies import copilot_async_session_factory
from luana_core_copilot.api.dto import ClientContextDTO
from luana_core_copilot.application.orchestrator.chat import CopilotOrchestrator
from luana_core_copilot.application.services.telegram_link_service import (
    consume_link_token,
    resolve_chat_id_to_tenant_user,
    touch_last_seen,
)
from luana_core_copilot.infrastructure.channels.telegram_bot import (
    CopilotTelegramBot,
)
from luana_core_copilot.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
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


async def process_copilot_telegram_turn(  # noqa: C901, PLR0911, PLR0912, PLR0915 — top-level turn coordinator (chat lookup → onboarding gate → orchestrator → format → send); breaking it apart fragments error semantics; PR-2 PI-5 cementado
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

            _LOGGER.info(
                "copilot_telegram_linked_message_received",
                tenant_id=str(link.tenant_id),
                user_id=str(link.user_id),
                chat_id_prefix=_mask_chat_id(chat_id),
                text_len_chars=len(text),
            )

            # Capture link metadata so the sync-session block below can
            # use it without holding a reference into the async-session
            # context manager (which closes when the outer ``async with``
            # exits the linked branch).
            link_tenant_id = link.tenant_id
            link_user_id = link.user_id

        # ── Sync-session block: orchestrator + ConversationRepository
        #     are sync Session-based; the link-service block above
        #     (AsyncSession) is already complete here. Per dependency-
        #     isolation iron rule (tessl__graceful-degradation), each
        #     external call below has its own try/except + fallback.
        from luana_core_platform.core.database import SessionLocal

        sync_db = SessionLocal()
        try:
            # 1) Conversation lookup-or-create per (tenant, user, channel='telegram', chat_id).
            try:
                conv_repo = ConversationRepository(sync_db)
                conv = conv_repo.get_or_create_by_channel(
                    tenant_id=link_tenant_id,
                    user_id=link_user_id,
                    channel_type="telegram",
                    channel_chat_id=chat_id,
                )
                sync_db.commit()
            except Exception as exc:  # noqa: BLE001 — per-dependency isolation
                sync_db.rollback()
                _LOGGER.warning(
                    "copilot_telegram_conv_lookup_failed",
                    tenant_id=str(link_tenant_id),
                    chat_id_prefix=_mask_chat_id(chat_id),
                    error=str(exc),
                )
                await bot.send_message(
                    chat_id=chat_id,
                    text=("No pude recuperar tu conversación en este momento. Probá de nuevo en un minuto."),
                )
                return

            # 2) Orchestrator invocation with channel='telegram' + 30s
            #    hard timeout (graceful-degradation Iron Rule).
            orchestrator = CopilotOrchestrator(sync_db)
            client_context = ClientContextDTO(channel="telegram", locale="es")
            try:
                result = await asyncio.wait_for(
                    orchestrator.invoke_text(
                        user_id=link_user_id,
                        tenant_id=link_tenant_id,
                        message=text,
                        conversation_id=str(conv.id),
                        channel="telegram",
                        context=client_context,
                    ),
                    timeout=30.0,
                )
            except TimeoutError:
                _LOGGER.warning(
                    "copilot_telegram_orchestrator_timeout",
                    tenant_id=str(link_tenant_id),
                    chat_id_prefix=_mask_chat_id(chat_id),
                )
                await bot.send_message(
                    chat_id=chat_id,
                    text=("Estoy tardando más de lo normal. Intentá de nuevo en un momento."),
                )
                return
            except Exception as exc:  # noqa: BLE001 — orchestrator resilience
                _LOGGER.warning(
                    "copilot_telegram_orchestrator_failed",
                    tenant_id=str(link_tenant_id),
                    chat_id_prefix=_mask_chat_id(chat_id),
                    error=str(exc),
                )
                await bot.send_message(
                    chat_id=chat_id,
                    text=("Tuve un problema procesando tu mensaje. Probá de nuevo."),
                )
                return

            # 3) Format adapter post-orchestrator (channel='telegram') —
            #    pure data transform, cannot fail (only string ops).
            formatted = format_for_channel_impl(
                content=result.response_text,
                channel_id="telegram",
            )
            text_to_send: str = str(formatted.get("content", "") or "")
            if not text_to_send:
                # invoke_text fallback already emitted a friendly message
                # via _user_facing_error_message; keep it as-is so the
                # user sees something.
                text_to_send = result.response_text or "No pude generar una respuesta. Probá reformular tu pregunta."

            # 4) Bot send — escape_markdown_v2 happens inside
            #    CopilotTelegramBot.send_message (PR-1).
            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=text_to_send,
                    parse_mode="MarkdownV2",
                )
            except Exception as exc:  # noqa: BLE001 — bot-send resilience
                _LOGGER.warning(
                    "copilot_telegram_bot_send_failed",
                    tenant_id=str(link_tenant_id),
                    chat_id_prefix=_mask_chat_id(chat_id),
                    error=str(exc),
                )
                return

            # 5) Observability log (best-effort, never raise).
            _LOGGER.info(
                "copilot_telegram_turn_completed",
                tenant_id=str(link_tenant_id),
                conversation_id=str(conv.id),
                chat_id_prefix=_mask_chat_id(chat_id),
                response_length=len(text_to_send),
                cache_read_tokens=result.cache_read_tokens,
                cache_creation_tokens=result.cache_creation_tokens,
                total_tokens=result.total_tokens,
                error_kind=result.error_kind,
            )
        finally:
            sync_db.close()

    except Exception as exc:
        # Graceful degradation — never raise to ARQ.
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
    from luana_core_platform.core.config import settings

    base = settings.FRONTEND_URL.rstrip("/")
    return f"{base}/settings/copilot/telegram"


def _mask_chat_id(chat_id: str) -> str:
    """First 5 chars + '***' for log redaction (anti-pattern A3)."""
    if len(chat_id) <= 5:
        return "***"
    return f"{chat_id[:5]}***"


__all__ = ["process_copilot_telegram_turn"]
