"""Read-only repository over analytics' official_metrics for advertising.

Same cross-module allowance as MetaCatalogRepository — advertising only
touches analytics infrastructure models, not its services/repositories.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select

from src.modules.analytics.infrastructure.models.official_metrics_model import (
    OfficialMetricModel,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


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
    """Slim read access to official_metrics filtered to Meta Ads."""

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


def resolve_period_window(period: str) -> tuple[date, date]:
    """Translate a '7d'|'30d'|'90d' period to a (start, end) date tuple."""
    today = date.today()
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(period, 30)
    start = today - timedelta(days=days - 1)
    return start, today
