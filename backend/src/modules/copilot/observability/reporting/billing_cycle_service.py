"""Billing cycle window resolver.

Tiny service: given a tenant + a date, return the (start, end_exclusive)
date range of the cycle the date belongs to. Anchor day comes from
``tenant_billing_config.billing_cycle_anchor_day`` and falls back to
:data:`compute_cycle_start_py.DEFAULT_ANCHOR_DAY` (25) when the tenant
has no config row.

Single source of truth for cycle math is :mod:`cycle_window`. This
service only adds the DB lookup of the anchor day.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from src.modules.copilot.observability.persistence.tenant_billing_config_repository import (
    TenantBillingConfigRepository,
)
from src.modules.copilot.observability.reporting.cycle_window import (
    DEFAULT_ANCHOR_DAY,
    compute_cycle_end_py,
    compute_cycle_start_py,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


def _today() -> dt.date:
    """Indirection for monkeypatching in tests. Always UTC."""
    return dt.datetime.now(tz=dt.UTC).date()


class BillingCycleService:
    """Resolve cycle windows + tenant currency for the reporting layer."""

    def __init__(self, db: Session) -> None:
        """Bind the service to a session."""
        self.db = db
        self._config_repo = TenantBillingConfigRepository(db)

    def compute_window(
        self,
        tenant_id: UUID,
        target_date: dt.date,
    ) -> tuple[dt.date, dt.date]:
        """Return ``(start_inclusive, end_exclusive)`` for the cycle of ``target_date``."""
        anchor = self._anchor_for(tenant_id)
        start = compute_cycle_start_py(anchor, target_date)
        end = compute_cycle_end_py(anchor, target_date)
        return start, end

    def current_cycle_window(self, tenant_id: UUID) -> tuple[dt.date, dt.date]:
        """Return the cycle window covering today."""
        return self.compute_window(tenant_id, _today())

    def previous_cycle_window(self, tenant_id: UUID) -> tuple[dt.date, dt.date]:
        """Return the cycle window immediately before the current one."""
        current_start, _ = self.current_cycle_window(tenant_id)
        anchor = self._anchor_for(tenant_id)
        # One day before the current cycle is guaranteed to fall in the
        # previous cycle.
        previous_anchor_date = current_start - dt.timedelta(days=1)
        start = compute_cycle_start_py(anchor, previous_anchor_date)
        end = compute_cycle_end_py(anchor, previous_anchor_date)
        return start, end

    def resolve_currency(self, tenant_id: UUID) -> str:
        """Return the tenant's billing currency, defaulting to USD."""
        config = self._config_repo.get(tenant_id=tenant_id)
        return config.billing_currency if config is not None else "USD"

    def _anchor_for(self, tenant_id: UUID) -> int:
        config = self._config_repo.get(tenant_id=tenant_id)
        if config is None:
            return DEFAULT_ANCHOR_DAY
        return int(config.billing_cycle_anchor_day)


__all__ = ["BillingCycleService"]
