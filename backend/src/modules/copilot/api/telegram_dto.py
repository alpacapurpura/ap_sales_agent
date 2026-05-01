"""Pydantic v2 DTOs for /api/v1/copilot/telegram/* endpoints.

PI-5 PR-1. ``response_model=`` obligatorio en cada endpoint
(rule ``pii-sanitisation``). Telegram inbound payload via
``TelegramUpdate`` filtered to private DMs only.

Reference: https://core.telegram.org/bots/api#update
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

# ── Inbound webhook (Telegram → us) ─────────────────────────────────────


class TelegramFrom(BaseModel):
    """Telegram message sender.

    ``first_name``/``last_name`` are PII — NOT persisted
    (D-PI5-030 anti-pattern A3).
    """

    model_config = ConfigDict(extra="ignore")
    id: int
    is_bot: bool = False
    username: str | None = None
    first_name: str | None = None  # NO persist
    last_name: str | None = None  # NO persist


class TelegramChat(BaseModel):
    """Telegram chat metadata.

    Filter ``type=='private'`` only (D-PI5-029 anti-pattern A11).
    """

    model_config = ConfigDict(extra="ignore")
    id: int
    type: Literal["private", "group", "supergroup", "channel"]


class TelegramMessage(BaseModel):
    """Inbound Telegram message envelope (subset of bot API)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    message_id: int
    from_: TelegramFrom = Field(alias="from")
    chat: TelegramChat
    text: str | None = None
    date: int  # Unix timestamp


class TelegramUpdate(BaseModel):
    """Telegram Bot API Update (subset).

    Only ``message`` field handled. Other update types (callback_query,
    inline_query, etc.) ignored at handler.

    Reference: https://core.telegram.org/bots/api#update
    """

    model_config = ConfigDict(extra="ignore")
    update_id: int
    message: TelegramMessage | None = None


class WebhookAck(BaseModel):
    """Always 200 OK to Telegram (D-PI5-026 NON-BLOCKING)."""

    model_config = ConfigDict(extra="forbid")
    ok: bool = True


# ── Magic link (web FE → us → bot) ──────────────────────────────────────


class LinkTokenRequest(BaseModel):
    """Empty body (auth via X-Tenant-ID + Clerk JWT)."""

    model_config = ConfigDict(extra="forbid")


class LinkTokenResponse(BaseModel):
    """Returned to FE. Plaintext token never persisted in DB."""

    model_config = ConfigDict(extra="forbid")
    token_id: UUID
    deep_link_url: HttpUrl  # t.me/<bot_username>?start=<token_plaintext>
    expires_at: datetime


class LinkStatusResponse(BaseModel):
    """Polled by FE every 3s x 60s.

    ``channel_user_id_masked``: first 5 chars + '***' (anti PII leak).
    """

    model_config = ConfigDict(extra="forbid")
    linked: bool
    channel_user_id_masked: str | None = None
    linked_at: datetime | None = None


class UnlinkResponse(BaseModel):
    """Soft delete (revoked_at set)."""

    model_config = ConfigDict(extra="forbid")
    revoked: bool = True
