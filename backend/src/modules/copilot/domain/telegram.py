"""Telegram channel domain entities for Copilot.

PI-5 PR-1 — bot global Nicolify (D-PI5-001), separación física vs
sales_agent (D-PI5-005). Cero acoplamiento con `modules/sales_agent/`
ni `modules/connections/.../telegram*`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ChannelType(StrEnum):
    """Canales soportados por copilot. MVP solo telegram.

    Future channels (whatsapp, etc.) se agregan aquí cuando los PIs
    siguientes los habiliten.
    """

    TELEGRAM = "telegram"


class ChannelLinkRole(StrEnum):
    """Roles per (tenant, channel_user). MVP solo owner.

    Schema preparado para multi-rol desde día 1 (D-PI5-017). Future
    roles (assistant, finance_admin, marketing_lead) se agregan en PI
    futuro cuando UI multi-rol llegue.
    """

    OWNER = "owner"


@dataclass(frozen=True, slots=True)
class ChannelLink:
    """Inmutable lookup row: chat_id ↔ tenant + user + role.

    Identity key = ``channel_user_id`` (Telegram ``from_user.id`` numeric
    como string — D-PI5-015). ``channel_username`` mutable, display only,
    NUNCA usar como FK (anti-pattern A4).
    """

    id: str  # UUID
    tenant_id: str
    user_id: str
    channel_type: ChannelType
    channel_user_id: str  # Telegram from_user.id (numeric as string)
    channel_username: str | None  # @handle (mutable, display only)
    role: ChannelLinkRole
    linked_at: datetime
    last_seen_at: datetime | None
    revoked_at: datetime | None  # soft delete


@dataclass(frozen=True, slots=True)
class LinkToken:
    """Single-use HMAC-SHA256 token for chat_id ↔ tenant linking.

    Hash stored in DB (NOT plaintext). TTL configurable via
    ``Settings.COPILOT_TELEGRAM_LINK_TOKEN_TTL_SECONDS`` (D-PI5-019).
    """

    id: str  # UUID
    token_hash: str  # SHA256 hex digest of HMAC(plaintext, API_SECRET_KEY)
    tenant_id: str
    user_id: str
    expires_at: datetime
    used_at: datetime | None
    created_at: datetime
