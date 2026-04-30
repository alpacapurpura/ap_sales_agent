"""Append-only audit trail for copilot_tenant_limits changes.

Table: copilot_tenant_limits_audit
Each upsert or soft_delete on copilot_tenant_limits inserts one row here,
within the same transaction (atomic audit).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class CopilotTenantLimitsAuditModel(Base):  # type: ignore[misc]
    """Append-only audit for copilot per-tenant limit changes.

    Q2 decision (architect): separate table to avoid write churn
    on the main table. Enables historical queries per tenant and
    human audit (Chris audits). Retention: unlimited in PR-1
    (low write rate — overrides change < 1/month/tenant).
    """

    __tablename__ = "copilot_tenant_limits_audit"

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
    action: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        comment="upsert | soft_delete",
    )
    voice_rpm_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    voice_rpm_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    media_max_bytes_before: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    media_max_bytes_after: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    changed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
