"""Read-only repository over analytics' official_metrics for advertising.

Same cross-module allowance as MetaCatalogRepository — advertising only
touches analytics infrastructure models, not its services/repositories.
This exception is explicitly granted in
`backend/tests/architecture/conftest.py` (CROSS_IMPORT_ALLOWED_SOURCES).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import structlog
from sqlalchemy import select

from src.modules.analytics.infrastructure.models.official_metrics_model import (
    OfficialMetricModel,
)
from src.modules.analytics.infrastructure.models.period_metrics_model import (
    PeriodMetricModel,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)


@dataclass
class MetricRow:
    metric_name: str
    value: float
    unit: str
    currency: str | None
    metric_date: date
    campaign_id: str | None
    ad_set_id: str | None
    ad_id: str | None


class MetricsRepository:
    """Slim read access to official_metrics + period_metrics filtered to Meta Ads."""

    DEFAULT_CHANNEL_SLUG = "meta-ads"

    def __init__(self, db: Session):
        self._db = db

    def detect_currency(
        self, tenant_id: UUID, channel_slug: str = DEFAULT_CHANNEL_SLUG
    ) -> str | None:
        """Return the currency recorded for the tenant's Meta ads metrics."""
        stmt = (
            select(OfficialMetricModel.currency)
            .where(
                OfficialMetricModel.tenant_id == tenant_id,
                OfficialMetricModel.channel_slug == channel_slug,
                OfficialMetricModel.currency.is_not(None),
            )
            .limit(1)
        )
        result = self._db.execute(stmt)
        return result.scalar_one_or_none()

    def load_rows(
        self,
        tenant_id: UUID,
        *,
        start_date: date,
        end_date: date,
        metric_names: list[str] | None = None,
        channel_slug: str = DEFAULT_CHANNEL_SLUG,
    ) -> list[MetricRow]:
        """Load official metric rows for the given window."""
        stmt = select(OfficialMetricModel).where(
            OfficialMetricModel.tenant_id == tenant_id,
            OfficialMetricModel.channel_slug == channel_slug,
            OfficialMetricModel.metric_date >= start_date,
            OfficialMetricModel.metric_date <= end_date,
        )
        if metric_names:
            stmt = stmt.where(OfficialMetricModel.metric_name.in_(metric_names))
        result = self._db.execute(stmt)
        rows: list[MetricRow] = []
        for m in result.scalars().all():
            rows.append(
                MetricRow(
                    metric_name=m.metric_name,
                    value=float(m.value or 0.0),
                    unit=m.unit,
                    currency=m.currency,
                    metric_date=m.metric_date,
                    campaign_id=m.campaign_id,
                    ad_set_id=m.ad_set_id,
                    ad_id=m.ad_id,
                )
            )
        return rows

    def list_period_metrics_for_reach(
        self,
        tenant_id: UUID,
        *,
        start_date: date,
        end_date: date,
        channel_slug: str = DEFAULT_CHANNEL_SLUG,
    ) -> list[PeriodMetricModel]:
        """Return all `reach` period_metrics rows overlapping the window.

        Loads both channel-level (`campaign_id IS NULL`) and per-campaign
        rows in a single query. The caller partitions them in memory:

        - `reach_all` ← channel-level row
        - `_compute_reach_for_campaigns` ← campaign-level rows by id

        Scoped to Meta Ads by default. Always filters by tenant_id.

        Predicate uses **overlap** semantics, not containment: any row whose
        `[period_start, period_end]` intersects the requested window is
        returned. Rationale — the ETL writes weekly/monthly/quarterly rows,
        so a containment predicate (`row fully within window`) would miss a
        monthly reach row for a 7d query, leaving reach as `None` for most
        real queries. Overlap returns the row, and the caller then picks the
        most recent matching row per partition (see service
        `_compute_reach_all` / `_compute_reach_for_campaigns`).

        The reach shown to the user therefore corresponds to the ETL-defined
        period that *covers* the requested window, not the exact window.
        This is the expected trade-off documented in the feature spec
        ("reach se actualiza al cierre del período").
        """
        stmt = (
            select(PeriodMetricModel)
            .where(
                PeriodMetricModel.tenant_id == tenant_id,
                PeriodMetricModel.channel_slug == channel_slug,
                PeriodMetricModel.metric_name == "reach",
                # Overlap: row intersects [start_date, end_date]
                PeriodMetricModel.period_start <= end_date,
                PeriodMetricModel.period_end >= start_date,
            )
            .order_by(PeriodMetricModel.period_start.desc())
        )
        return list(self._db.execute(stmt).scalars().all())


def resolve_period_window(
    period: str,
    tz: str = "UTC",
) -> tuple[date, date]:
    """Translate a '7d'|'30d'|'90d' period to a (start, end) tuple.

    Uses the tenant's timezone to compute "today" — critical for tenants
    far from UTC (e.g., `America/Lima` UTC-5) where `date.today()` would
    be off-by-one near midnight UTC.

    Falls back to UTC when `tz` is invalid. The fallback logs a single
    structlog warning — callers passing an invalid timezone will continue
    to work, they just get UTC semantics.
    """
    try:
        tenant_tz = ZoneInfo(tz)
    except (ZoneInfoNotFoundError, ValueError, TypeError) as exc:
        logger.warning(
            "resolve_period_window_invalid_tz",
            tz=tz,
            error=str(exc),
        )
        tenant_tz = ZoneInfo("UTC")

    today = datetime.now(tenant_tz).date()
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(period, 30)
    start = today - timedelta(days=days - 1)
    return start, today
