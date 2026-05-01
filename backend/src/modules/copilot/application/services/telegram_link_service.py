"""HMAC-SHA256 magic link service for Copilot Telegram channel.

D-PI5-019..022. Plaintext token returned ONCE to caller; only hash
stored in DB. Single-use enforced via ``used_at`` UNIQUE constraint.
TTL configurable via ``Settings.COPILOT_TELEGRAM_LINK_TOKEN_TTL_SECONDS``.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select

from src.core.config import settings
from src.modules.copilot.infrastructure.models.telegram_models import (
    CopilotChannelLinkModel,
    CopilotLinkTokenModel,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

_LOGGER = structlog.get_logger(__name__)


# ── Token generation / validation ──────────────────────────────────────────


def generate_link_token(tenant_id: UUID, user_id: UUID) -> tuple[str, str, datetime]:
    """Generate plaintext token + hash + expires_at.

    Returns ``(plaintext_token, token_hash, expires_at)``. Plaintext
    returned ONCE — caller embeds in deep_link_url and discards. Hash
    stored in DB.
    """
    plaintext = secrets.token_urlsafe(32)
    token_hash = hash_token_plaintext(plaintext)
    expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.COPILOT_TELEGRAM_LINK_TOKEN_TTL_SECONDS,
    )
    return plaintext, token_hash, expires_at


def hash_token_plaintext(plaintext: str) -> str:
    """HMAC-SHA256 hex digest of plaintext token using app secret.

    Used both at generation (store hash) and validation (compute hash
    of inbound /start TOKEN, compare DB).
    """
    return hmac.new(
        settings.API_SECRET_KEY.encode(),
        plaintext.encode(),
        hashlib.sha256,
    ).hexdigest()


def build_deep_link_url(plaintext_token: str) -> str:
    """Build ``t.me/<bot_username>?start=<plaintext>`` deep link.

    Reference: https://core.telegram.org/bots/features#deep-linking
    """
    return f"https://t.me/{settings.COPILOT_TELEGRAM_BOT_USERNAME}?start={plaintext_token}"


# ── DB operations (AsyncSession) ───────────────────────────────────────────


async def create_link_token(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    token_hash: str,
    expires_at: datetime,
) -> UUID:
    """Persist hash + return new token_id."""
    row = CopilotLinkTokenModel(
        token_hash=token_hash,
        tenant_id=tenant_id,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(row)
    await db.flush()
    await db.commit()
    return row.id


async def fetch_link_status(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    token_id: UUID | None = None,
) -> dict:
    """Return current link status for (tenant, user).

    If ``token_id`` given: validate token tenant/user match (auth guard).
    Always returns latest non-revoked link for (tenant, user) — independent
    of which token triggered it.
    """
    if token_id is not None:
        token_stmt = (
            select(CopilotLinkTokenModel)
            .where(CopilotLinkTokenModel.id == token_id)
            .where(CopilotLinkTokenModel.tenant_id == tenant_id)
            .where(CopilotLinkTokenModel.user_id == user_id)
        )
        token_result = await db.execute(token_stmt)
        token = token_result.scalar_one_or_none()
        if token is None:
            return {
                "linked": False,
                "channel_user_id_masked": None,
                "linked_at": None,
            }

    link_stmt = (
        select(CopilotChannelLinkModel)
        .where(CopilotChannelLinkModel.tenant_id == tenant_id)
        .where(CopilotChannelLinkModel.user_id == user_id)
        .where(CopilotChannelLinkModel.channel_type == "telegram")
        .where(CopilotChannelLinkModel.revoked_at.is_(None))
        .order_by(CopilotChannelLinkModel.linked_at.desc())
        .limit(1)
    )
    link_result = await db.execute(link_stmt)
    link = link_result.scalar_one_or_none()
    if link is None:
        return {
            "linked": False,
            "channel_user_id_masked": None,
            "linked_at": None,
        }
    return {
        "linked": True,
        "channel_user_id_masked": _mask_chat_id(link.channel_user_id),
        "linked_at": link.linked_at,
    }


async def consume_link_token(
    db: AsyncSession,
    *,
    plaintext_token: str,
    channel_user_id: str,
    channel_username: str | None,
) -> CopilotChannelLinkModel | None:
    """Validate /start TOKEN inbound and bind chat_id ↔ tenant.

    Returns the new ``CopilotChannelLinkModel`` row if token valid,
    or ``None`` if invalid/expired/used.

    Atomicity: token marked ``used_at`` BEFORE link insert. Race
    condition mitigated by UNIQUE(token_hash) — duplicate token use
    raises IntegrityError caught upstream.
    """
    token_hash = hash_token_plaintext(plaintext_token)
    now = datetime.now(timezone.utc)

    stmt = (
        select(CopilotLinkTokenModel)
        .where(CopilotLinkTokenModel.token_hash == token_hash)
        .where(CopilotLinkTokenModel.expires_at > now)
        .where(CopilotLinkTokenModel.used_at.is_(None))
    )
    result = await db.execute(stmt)
    token = result.scalar_one_or_none()
    if token is None:
        _LOGGER.info("copilot_telegram_link_token_invalid_or_expired")
        return None

    # Mark token consumed (single-use)
    token.used_at = now

    # Check if existing link for this (tenant, telegram, chat_id) — re-link
    existing_stmt = (
        select(CopilotChannelLinkModel)
        .where(CopilotChannelLinkModel.tenant_id == token.tenant_id)
        .where(CopilotChannelLinkModel.channel_type == "telegram")
        .where(CopilotChannelLinkModel.channel_user_id == channel_user_id)
    )
    existing_result = await db.execute(existing_stmt)
    existing = existing_result.scalar_one_or_none()

    if existing is not None:
        # Re-link case: clear revoked_at + update user
        existing.user_id = token.user_id
        existing.channel_username = channel_username
        existing.linked_at = now
        existing.revoked_at = None
        existing.last_seen_at = now
        link = existing
    else:
        link = CopilotChannelLinkModel(
            tenant_id=token.tenant_id,
            user_id=token.user_id,
            channel_type="telegram",
            channel_user_id=channel_user_id,
            channel_username=channel_username,
            role="owner",  # MVP — D-PI5-017
            linked_at=now,
            last_seen_at=now,
        )
        db.add(link)

    await db.flush()
    await db.commit()
    _LOGGER.info(
        "copilot_telegram_link_bound",
        tenant_id=str(token.tenant_id),
        user_id=str(token.user_id),
        chat_id_prefix=_mask_chat_id(channel_user_id),
    )
    return link


async def resolve_chat_id_to_tenant_user(
    db: AsyncSession,
    *,
    channel_user_id: str,
    channel_type: str = "telegram",
) -> CopilotChannelLinkModel | None:
    """Webhook worker uses this to resolve ``chat_id → (tenant, user, role)``.

    Returns ``None`` if unlinked (caller sends CTA template).
    """
    stmt = (
        select(CopilotChannelLinkModel)
        .where(CopilotChannelLinkModel.channel_type == channel_type)
        .where(CopilotChannelLinkModel.channel_user_id == channel_user_id)
        .where(CopilotChannelLinkModel.revoked_at.is_(None))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def revoke_chat_link(db: AsyncSession, *, tenant_id: UUID, user_id: UUID) -> int:
    """Soft delete current Telegram link for (tenant, user)."""
    now = datetime.now(timezone.utc)
    stmt = (
        select(CopilotChannelLinkModel)
        .where(CopilotChannelLinkModel.tenant_id == tenant_id)
        .where(CopilotChannelLinkModel.user_id == user_id)
        .where(CopilotChannelLinkModel.channel_type == "telegram")
        .where(CopilotChannelLinkModel.revoked_at.is_(None))
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    for row in rows:
        row.revoked_at = now
    await db.flush()
    await db.commit()
    return len(rows)


async def touch_last_seen(db: AsyncSession, link_id: UUID) -> None:
    """Update last_seen_at on every successful turn."""
    now = datetime.now(timezone.utc)
    stmt = select(CopilotChannelLinkModel).where(CopilotChannelLinkModel.id == link_id)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()
    if link is not None:
        link.last_seen_at = now
        await db.flush()
        await db.commit()


# ── Helpers ────────────────────────────────────────────────────────────────


def _mask_chat_id(chat_id: str) -> str:
    """Mask Telegram chat_id for display/logging.

    Show first 5 chars + '***'. Anti-pattern A3 PII protection.
    Example: ``"123456789"`` → ``"12345***"``.
    """
    if len(chat_id) <= 5:
        return "***"
    return f"{chat_id[:5]}***"
