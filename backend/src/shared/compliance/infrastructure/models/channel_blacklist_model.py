"""SQLAlchemy 2.0 model for channel_blacklist.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
import uuid as uuid_mod
from uuid import UUID

from sqlalchemy import DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class ChannelBlacklistModel(Base):
    """channel_blacklist table — per-tenant per-channel contact blacklist.

    Soft-deleted via deleted_at (hard delete prohibited).
    Unique constraint (tenant_id, channel, identifier) prevents duplicate entries.
    Identifier should be normalized by caller (E.164 for phone, lowercase for email).
    """

    __tablename__ = "channel_blacklist"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_mod.uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_by_user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "channel",
            "identifier",
            name="uq_channel_blacklist_tenant_channel_identifier",
        ),
        Index(
            "ix_channel_blacklist_lookup",
            "tenant_id",
            "channel",
            "identifier",
            postgresql_where="deleted_at IS NULL",
        ),
    )
