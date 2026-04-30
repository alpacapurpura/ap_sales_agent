"""SQLAlchemy 2.0 model for copilot per-tenant limit overrides.

Table: copilot_tenant_limits
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class CopilotTenantLimitsModel(Base):  # type: ignore[misc]
    """Per-tenant overrides for copilot rate limits and media caps.

    One optional row per tenant. Absence = tenant uses env defaults.
    Soft-delete only: set deleted_at = now() to revert tenant to defaults.
    """

    __tablename__ = "copilot_tenant_limits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    voice_rpm_override: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    media_max_bytes_override: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
