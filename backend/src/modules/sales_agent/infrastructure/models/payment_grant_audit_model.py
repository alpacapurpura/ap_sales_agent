"""Payment grant audit SA model — S9 (append-only).

One row per access-delivery attempt. The UNIQUE constraint on the
natural key (tenant_id, lead_id, offer_id, payment_id) guarantees
idempotent grant_access: second call returns the existing row.

Append-only invariant:
- No updated_at column.
- Arch test ``test_payment_grant_audit_model_has_no_updated_at`` enforces.
- Only the retention worker may DELETE expired rows.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class PaymentGrantAuditModel(Base):
    """Append-only log of every access-delivery attempt."""

    __tablename__ = "payment_grant_audit"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    lead_id = Column(UUID(as_uuid=True), nullable=False)
    offer_id = Column(UUID(as_uuid=True), nullable=False)
    payment_id = Column(UUID(as_uuid=True), nullable=False)
    channels = Column(JSONB, nullable=False, default=list, server_default="[]")
    status = Column(String(50), nullable=False, default="granted")
    failure_detail = Column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    # NOTE: No updated_at — this table is append-only.

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "lead_id",
            "offer_id",
            "payment_id",
            name="uq_payment_grant_natural_key",
        ),
        Index("ix_payment_grant_audit_tenant", "tenant_id", "created_at"),
    )
