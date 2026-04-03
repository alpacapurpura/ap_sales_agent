"""Repository for period_metrics table — deduplicated multi-day period data.

Handles NON_AGGREGABLE metrics that are extracted directly from APIs
at weekly/monthly/quarterly granularity.
"""

import json
import uuid
from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from src.modules.analytics.infrastructure.models.period_metrics_model import (
    PeriodMetricModel,
)


class PeriodMetricsRepository:
    """CRUD operations for the period_metrics table."""

    def __init__(self, db: Session):
        self.db = db

    _UPSERT_SQL = text("""
        INSERT INTO period_metrics (
            id, tenant_id, provider, channel_slug, metric_name,
            value, unit, currency, period_type, period_start, period_end,
            campaign_id, ad_set_id, ad_id,
            cost_type, extra, source_extraction_run_id, created_at, updated_at
        ) VALUES (
            :id, :tenant_id, :provider, :channel_slug, :metric_name,
            :value, :unit, :currency, :period_type, :period_start, :period_end,
            :campaign_id, :ad_set_id, :ad_id,
            :cost_type, :extra::jsonb, :source_extraction_run_id, NOW(), NOW()
        )
        ON CONFLICT (
            tenant_id, provider, channel_slug, metric_name,
            period_type, period_start,
            COALESCE(campaign_id, ''), COALESCE(ad_set_id, ''), COALESCE(ad_id, '')
        )
        DO UPDATE SET
            value = EXCLUDED.value,
            unit = EXCLUDED.unit,
            currency = EXCLUDED.currency,
            period_end = EXCLUDED.period_end,
            cost_type = EXCLUDED.cost_type,
            extra = EXCLUDED.extra,
            source_extraction_run_id = EXCLUDED.source_extraction_run_id,
            updated_at = NOW()
    """)

    def upsert_period_metrics(self, metrics: list[dict]) -> int:
        """Upsert period metrics using ON CONFLICT DO UPDATE.

        Returns the number of rows upserted.
        """
        if not metrics:
            return 0

        count = 0
        for m in metrics:
            if "id" not in m:
                m["id"] = uuid.uuid4()
            params = {
                "id": m["id"],
                "tenant_id": m["tenant_id"],
                "provider": m["provider"],
                "channel_slug": m["channel_slug"],
                "metric_name": m["metric_name"],
                "value": m["value"],
                "unit": m["unit"],
                "currency": m.get("currency"),
                "period_type": m["period_type"],
                "period_start": m["period_start"],
                "period_end": m["period_end"],
                "campaign_id": m.get("campaign_id"),
                "ad_set_id": m.get("ad_set_id"),
                "ad_id": m.get("ad_id"),
                "cost_type": m.get("cost_type"),
                "extra": json.dumps(m.get("extra") or {}),
                "source_extraction_run_id": m.get("source_extraction_run_id"),
            }
            self.db.execute(self._UPSERT_SQL, params)
            count += 1

        self.db.flush()
        return count

    def get_period_metrics(
        self,
        tenant_id: UUID,
        channel_slug: Optional[str] = None,
        metric_name: Optional[str] = None,
        period_type: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[PeriodMetricModel]:
        """Query period metrics with optional filters."""
        stmt = select(PeriodMetricModel).where(
            PeriodMetricModel.tenant_id == tenant_id
        )
        if channel_slug is not None:
            stmt = stmt.where(PeriodMetricModel.channel_slug == channel_slug)
        if metric_name is not None:
            stmt = stmt.where(PeriodMetricModel.metric_name == metric_name)
        if period_type is not None:
            stmt = stmt.where(PeriodMetricModel.period_type == period_type)
        if start_date is not None:
            stmt = stmt.where(PeriodMetricModel.period_start >= start_date)
        if end_date is not None:
            stmt = stmt.where(PeriodMetricModel.period_end <= end_date)

        stmt = stmt.order_by(PeriodMetricModel.period_start.desc())
        return list(self.db.execute(stmt).scalars().all())

    def get_existing_periods(
        self,
        tenant_id: UUID,
        provider: str,
        period_type: str,
        start_date: date,
        end_date: date,
    ) -> set[date]:
        """Return period_start dates that already have data (for gap detection)."""
        stmt = (
            select(PeriodMetricModel.period_start)
            .where(
                PeriodMetricModel.tenant_id == tenant_id,
                PeriodMetricModel.provider == provider,
                PeriodMetricModel.period_type == period_type,
                PeriodMetricModel.period_start >= start_date,
                PeriodMetricModel.period_start <= end_date,
            )
            .distinct()
        )
        return {row for row in self.db.execute(stmt).scalars().all()}
