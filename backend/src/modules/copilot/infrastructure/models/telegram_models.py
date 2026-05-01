"""SQLAlchemy 2.0 models for Copilot Telegram channel.

PI-5 PR-1. Schema separado de ``sales_agent_*`` por D-PI5-005.
Arch fitness test ``test_copilot_channel_links_no_cross_module_fk``
enforce zero FK hacia sales_agent_*.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from src.shared.domain.base_entity import Base


class CopilotChannelLinkModel(Base):
    """Persistencia ``ChannelLink`` (chat_id ↔ tenant + user + role)."""

    __tablename__ = "copilot_channel_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    channel_type = Column(String(32), nullable=False)
    # Telegram from_user.id stored as string (anti-overflow JSON safe)
    channel_user_id = Column(String(64), nullable=False)
    # @username mutable, display only — NUNCA usar como FK (D-PI5-015)
    channel_username = Column(String(64), nullable=True)
    role = Column(String(32), nullable=False, default="owner", server_default="owner")
    linked_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        """Debug repr."""
        return (
            f"<CopilotChannelLink id={self.id} tenant={self.tenant_id} "
            f"channel={self.channel_type} chat_user={self.channel_user_id}>"
        )


class CopilotLinkTokenModel(Base):
    """Persistencia ``LinkToken`` (single-use HMAC magic link)."""

    __tablename__ = "copilot_link_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # SHA256 hex of HMAC(plaintext, API_SECRET_KEY) — NUNCA plaintext
    token_hash = Column(String(128), nullable=False, unique=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:  # pragma: no cover
        """Debug repr."""
        return f"<CopilotLinkToken id={self.id} tenant={self.tenant_id} used={self.used_at is not None}>"
