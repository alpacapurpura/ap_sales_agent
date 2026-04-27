"""Repository for ``tenant_billing_config``.

Filtered by ``tenant_id`` (PK) so cross-tenant leak is structurally
impossible.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select

from src.modules.copilot.observability.persistence.models.tenant_billing_config_model import (
    TenantBillingConfigModel,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class TenantBillingConfigRepository:
    """Persist and query the per-tenant billing config."""

    def __init__(self, db: Session) -> None:
        """Bind the repository to a session."""
        self.db = db

    def get(self, *, tenant_id: UUID) -> TenantBillingConfigModel | None:
        """Return the row for ``tenant_id`` or ``None`` if unconfigured."""
        stmt = select(TenantBillingConfigModel).where(
            TenantBillingConfigModel.tenant_id == tenant_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def upsert(
        self,
        *,
        tenant_id: UUID,
        billing_cycle_anchor_day: int,
        billing_currency: str,
        fx_source: str,
        flat_fee_amount: object | None = None,
        cost_alert_threshold_usd: object | None = None,
        notes: str | None = None,
    ) -> TenantBillingConfigModel:
        """Insert or update the config for ``tenant_id``.

        Performed in two ORM steps (no Postgres-specific ``ON CONFLICT``)
        so SQLite tests roundtrip without dialect detection. The unique
        primary key on ``tenant_id`` keeps the call idempotent.
        """
        existing = self.get(tenant_id=tenant_id)
        if existing is None:
            row = TenantBillingConfigModel(
                tenant_id=tenant_id,
                billing_cycle_anchor_day=billing_cycle_anchor_day,
                billing_currency=billing_currency,
                fx_source=fx_source,
                flat_fee_amount=flat_fee_amount,
                cost_alert_threshold_usd=cost_alert_threshold_usd,
                notes=notes,
            )
            self.db.add(row)
            return row

        existing.billing_cycle_anchor_day = billing_cycle_anchor_day
        existing.billing_currency = billing_currency
        existing.fx_source = fx_source
        existing.flat_fee_amount = flat_fee_amount
        existing.cost_alert_threshold_usd = cost_alert_threshold_usd
        existing.notes = notes
        return existing
