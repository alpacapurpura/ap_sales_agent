"""SQLAlchemy model for ``tenant_billing_config``.

Per-tenant billing cycle anchor day (default 25 — Nicolify cycle is
25→25), billing currency (default USD) and FX source (default
frankfurter).
"""

from __future__ import annotations

from sqlalchemy import CHAR, Column, DateTime, Numeric, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class TenantBillingConfigModel(Base):
    """ORM mapping for ``tenant_billing_config``."""

    __tablename__ = "tenant_billing_config"

    tenant_id = Column(UUID(as_uuid=True), primary_key=True)
    billing_cycle_anchor_day = Column(SmallInteger, nullable=False, default=25)
    billing_currency = Column(CHAR(3), nullable=False, default="USD")
    fx_source = Column(String(32), nullable=False, default="frankfurter")
    flat_fee_amount = Column(Numeric(14, 2), nullable=True)
    cost_alert_threshold_usd = Column(Numeric(14, 2), nullable=True)
    notes = Column(Text, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        default=func.now(),
    )

    def __repr__(self) -> str:
        """Return a debug-friendly summary of the config."""
        return (
            f"<TenantBillingConfig tenant_id={self.tenant_id} "
            f"anchor={self.billing_cycle_anchor_day} cur={self.billing_currency}>"
        )
