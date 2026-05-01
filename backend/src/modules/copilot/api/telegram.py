"""Copilot Telegram webhook + magic link endpoints.

PI-5 PR-1. D-PI5-026 NON-BLOCKING webhook + D-PI5-028 secret_token
validation + D-PI5-029 private chats only + D-PI5-030 sanitize PII
before persist/log.

Endpoints:
- POST /api/v1/copilot/telegram/webhook (Telegram → us, secret_token auth)
- POST /api/v1/copilot/telegram/link-tokens (Clerk auth, generate magic link)
- GET  /api/v1/copilot/telegram/link-status (Clerk auth, FE polling)
- DELETE /api/v1/copilot/telegram/link (Clerk auth, soft delete)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Annotated

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

if TYPE_CHECKING:
    from uuid import UUID
else:
    from uuid import UUID  # runtime — used in Query annotation
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.arq_pool import get_arq_pool
from src.core.config import settings
from src.modules.copilot.api._dependencies import get_copilot_async_session
from src.modules.copilot.api.telegram_dto import (
    LinkStatusResponse,
    LinkTokenRequest,
    LinkTokenResponse,
    TelegramUpdate,
    UnlinkResponse,
    WebhookAck,
)
from src.modules.copilot.application.services.telegram_link_service import (
    build_deep_link_url,
    create_link_token,
    fetch_link_status,
    generate_link_token,
    revoke_chat_link,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.shared.agent_observability.recording.sanitization import sanitize_payload

router = APIRouter(prefix="/api/v1/copilot/telegram", tags=["copilot-telegram"])
_LOGGER = structlog.get_logger(__name__)


@router.post(
    "/webhook",
    response_model=WebhookAck,
    status_code=status.HTTP_200_OK,
)
async def copilot_telegram_webhook(
    update: TelegramUpdate,
    x_telegram_bot_api_secret_token: Annotated[str | None, Header()] = None,
) -> WebhookAck:
    """Telegram → Nicolify webhook. NON-BLOCKING enqueue ARQ.

    Security:
    - D-PI5-028: validate ``X-Telegram-Bot-Api-Secret-Token`` header
      vs ``settings.COPILOT_TELEGRAM_WEBHOOK_SECRET_TOKEN``. 401 strict.
    - D-PI5-029: filter ``chat.type=='private'`` (anti-pattern A11).
    - D-PI5-030: sanitize PII before persist/log (anti-pattern A3).

    Performance:
    - D-PI5-026: returns 200 in < 200ms (anti-pattern A8 — Telegram retry).
      LLM processing happens async in ARQ worker.
    """
    expected = settings.COPILOT_TELEGRAM_WEBHOOK_SECRET_TOKEN
    if not expected or x_telegram_bot_api_secret_token != expected:
        _LOGGER.warning("copilot_telegram_webhook_unauthorized")
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing X-Telegram-Bot-Api-Secret-Token",
        )

    msg = update.message
    if msg is None or msg.chat.type != "private":
        # Silent ignore (still 200 to Telegram so they don't retry)
        _LOGGER.info(
            "copilot_telegram_webhook_non_private_ignored",
            update_id=update.update_id,
            chat_type=msg.chat.type if msg else "no_message",
        )
        return WebhookAck()

    # D-PI5-030 sanitize PII before persist — drop username/first_name/last_name/phone
    payload = sanitize_payload(
        {
            "update_id": update.update_id,
            "chat_id": str(msg.chat.id),
            "message_id": msg.message_id,
            "text": msg.text or "",
            "username": msg.from_.username,  # mutable display only
            "received_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    _LOGGER.info(
        "copilot_telegram_webhook_received",
        update_id=update.update_id,
        chat_type="private",
        text_len_chars=len(msg.text or ""),
    )

    pool = get_arq_pool()
    if pool is None:
        # Graceful degradation — log + still ack (avoid Telegram retries)
        _LOGGER.warning(
            "copilot_telegram_arq_pool_unavailable",
            update_id=update.update_id,
        )
        return WebhookAck()

    try:
        await pool.enqueue_job("process_copilot_telegram_turn", payload)
    except Exception as exc:  # noqa: BLE001 — graceful degradation, never raise to Telegram
        _LOGGER.warning(
            "copilot_telegram_enqueue_failed",
            update_id=update.update_id,
            error=str(exc),
        )

    return WebhookAck()


@router.post(
    "/link-tokens",
    response_model=LinkTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_telegram_link_token(
    body: LinkTokenRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_copilot_async_session)],
) -> LinkTokenResponse:
    """Generate magic link for user to bind their Telegram chat.

    D-PI5-019: HMAC-SHA256, TTL 15 min, single-use, hash stored in DB
    (NOT plaintext).
    """
    plaintext, token_hash, expires_at = generate_link_token(
        tenant_id=user.tenant_id,
        user_id=user.id,
    )
    token_id = await create_link_token(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    deep_link = build_deep_link_url(plaintext)
    _LOGGER.info(
        "copilot_telegram_link_created",
        tenant_id=str(user.tenant_id),
        user_id=str(user.id),
        token_id=str(token_id),
    )
    return LinkTokenResponse(
        token_id=token_id,
        deep_link_url=deep_link,
        expires_at=expires_at,
    )


@router.get(
    "/link-status",
    response_model=LinkStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_telegram_link_status(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_copilot_async_session)],
    token_id: Annotated[UUID | None, Query()] = None,
) -> LinkStatusResponse:
    """Return current Telegram link state for (tenant, user).

    FE polls this every 3s x 60s during onboarding flow with
    ``token_id`` query param. Without ``token_id`` returns current
    state (used by ``useTelegramCurrentLink`` hook).
    """
    status_data = await fetch_link_status(
        db,
        tenant_id=user.tenant_id,
        user_id=user.id,
        token_id=token_id,
    )
    return LinkStatusResponse(**status_data)


@router.delete(
    "/link",
    response_model=UnlinkResponse,
    status_code=status.HTTP_200_OK,
)
async def unlink_telegram(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_copilot_async_session)],
) -> UnlinkResponse:
    """Soft delete current Telegram link (set ``revoked_at``)."""
    revoked_count = await revoke_chat_link(db, tenant_id=user.tenant_id, user_id=user.id)
    _LOGGER.info(
        "copilot_telegram_link_unbound",
        tenant_id=str(user.tenant_id),
        user_id=str(user.id),
        revoked_count=revoked_count,
    )
    return UnlinkResponse()
