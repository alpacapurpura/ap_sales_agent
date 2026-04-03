"""Repository for official_metrics table — validated dashboard data.

Official metrics are the source of truth for dashboard queries.
They are promoted from staging_metrics after transformation.
"""

import json
import uuid
from collections import defaultdict
from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from src.modules.analytics.domain.enums import AggregationType
from src.modules.analytics.domain.metric_catalog import get_metric_def
from src.modules.analytics.infrastructure.models.official_metrics_model import (
    OfficialMetricModel,
)


class OfficialMetricsRepository:
    """CRUD operations for the official_metrics table."""

    def __init__(self, db: Session):
        self.db = db

    _UPSERT_FROM_STAGING_SQL = text("""
        INSERT INTO official_metrics (
            id, tenant_id, provider, channel_slug, metric_name,
            value, unit, currency, metric_date, spend, revenue,
            campaign_id, ad_set_id, ad_id,
            cost_type, extra, source_extraction_run_id, created_at, updated_at
        ) VALUES (
            :id, :tenant_id, :provider, :channel_slug, :metric_name,
            :value, :unit, :currency, :metric_date, :spend, :revenue,
            :campaign_id, :ad_set_id, :ad_id,
            :cost_type, :extra::jsonb, :source_extraction_run_id, NOW(), NOW()
        )
        ON CONFLICT (
            tenant_id, provider, channel_slug, metric_name, metric_date,
            COALESCE(campaign_id, ''), COALESCE(ad_set_id, ''), COALESCE(ad_id, '')
        )
        DO UPDATE SET
            value = EXCLUDED.value,
            unit = EXCLUDED.unit,
            currency = EXCLUDED.currency,
            spend = EXCLUDED.spend,
            revenue = EXCLUDED.revenue,
            cost_type = EXCLUDED.cost_type,
            extra = EXCLUDED.extra,
            source_extraction_run_id = EXCLUDED.source_extraction_run_id,
            updated_at = NOW()
    """)

    def upsert_from_staging(self, metrics: List[dict]) -> int:
        """Insert or update official metrics from transformed staging data.

        Uses PostgreSQL ON CONFLICT DO UPDATE on the composite key
        (tenant_id, provider, channel_slug, metric_name, metric_date,
         COALESCE(campaign_id, ''), COALESCE(ad_set_id, ''), COALESCE(ad_id, ''))
        to deduplicate. Raw SQL is required because SQLAlchemy's
        on_conflict_do_update does not support COALESCE expressions in
        index_elements.

        Returns the number of rows upserted.
        """
        if not metrics:
            return 0

        count = 0
        for metric_data in metrics:
            # Ensure id is set
            if "id" not in metric_data:
                metric_data["id"] = uuid.uuid4()

            params = {
                "id": metric_data["id"],
                "tenant_id": metric_data["tenant_id"],
                "provider": metric_data["provider"],
                "channel_slug": metric_data["channel_slug"],
                "metric_name": metric_data["metric_name"],
                "value": metric_data.get("value"),
                "unit": metric_data.get("unit"),
                "currency": metric_data.get("currency"),
                "metric_date": metric_data.get("metric_date"),
                "spend": metric_data.get("spend"),
                "revenue": metric_data.get("revenue"),
                "campaign_id": metric_data.get("campaign_id"),
                "ad_set_id": metric_data.get("ad_set_id"),
                "ad_id": metric_data.get("ad_id"),
                "cost_type": metric_data.get("cost_type"),
                "extra": json.dumps(metric_data.get("extra") or {}),
                "source_extraction_run_id": metric_data.get("source_extraction_run_id"),
            }
            self.db.execute(self._UPSERT_FROM_STAGING_SQL, params)
            count += 1

        self.db.flush()
        return count

    def get_metrics(
        self,
        tenant_id: UUID,
        channel_slug: Optional[str] = None,
        metric_name: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[OfficialMetricModel]:
        """Flexible query with optional filters for dashboard display."""
        stmt = select(OfficialMetricModel).where(
            OfficialMetricModel.tenant_id == tenant_id
        )

        if channel_slug is not None:
            stmt = stmt.where(OfficialMetricModel.channel_slug == channel_slug)
        if metric_name is not None:
            stmt = stmt.where(OfficialMetricModel.metric_name == metric_name)
        if start_date is not None:
            stmt = stmt.where(OfficialMetricModel.metric_date >= start_date)
        if end_date is not None:
            stmt = stmt.where(OfficialMetricModel.metric_date <= end_date)

        stmt = stmt.order_by(OfficialMetricModel.metric_date.desc())
        return list(self.db.execute(stmt).scalars().all())

    def get_existing_dates(
        self,
        tenant_id: UUID,
        provider: str,
        start_date: date,
        end_date: date,
    ) -> set[date]:
        """Return dates that already have data for this tenant+provider."""
        stmt = (
            select(OfficialMetricModel.metric_date)
            .where(
                OfficialMetricModel.tenant_id == tenant_id,
                OfficialMetricModel.provider == provider,
                OfficialMetricModel.metric_date >= start_date,
                OfficialMetricModel.metric_date <= end_date,
            )
            .distinct()
        )
        return {row for row in self.db.execute(stmt).scalars().all()}

    def get_channel_summary(
        self,
        tenant_id: UUID,
        stage_slug: str,
        period_type: str = "last_30_days",
    ) -> List:
        """Aggregated metrics for dashboard display.

        Returns channel-level summaries for the given stage and period.
        Delegates to metric_aggregations table for pre-computed data.
        """
        from src.modules.analytics.infrastructure.models.metric_aggregation_model import (
            MetricAggregationModel,
        )

        stmt = (
            select(MetricAggregationModel)
            .where(
                MetricAggregationModel.tenant_id == tenant_id,
                MetricAggregationModel.period_type == period_type,
            )
            .order_by(MetricAggregationModel.channel_slug)
        )
        return list(self.db.execute(stmt).scalars().all())

    def upsert_increment(
        self,
        tenant_id: UUID,
        provider: str,
        channel_slug: str,
        metric_name: str,
        value: float,
        unit: str,
        metric_date: date,
        cost_type: str | None = None,
        extra: dict | None = None,
        campaign_id: str | None = None,
        ad_set_id: str | None = None,
        ad_id: str | None = None,
    ) -> None:
        """Upsert with SUM semantics: increment value if row exists, insert otherwise.

        Used by webhook-fed providers (ManyChat) where each event adds to the daily total.
        Uses COALESCE-based unique index for campaign-level dimension support.
        """
        sql = text("""
            INSERT INTO official_metrics (
                id, tenant_id, provider, channel_slug, metric_name,
                value, unit, metric_date, cost_type, extra,
                campaign_id, ad_set_id, ad_id,
                created_at, updated_at
            ) VALUES (
                gen_random_uuid(), :tenant_id, :provider, :channel_slug, :metric_name,
                :value, :unit, :metric_date, :cost_type, :extra::jsonb,
                :campaign_id, :ad_set_id, :ad_id,
                NOW(), NOW()
            )
            ON CONFLICT (
                tenant_id, provider, channel_slug, metric_name, metric_date,
                COALESCE(campaign_id, ''), COALESCE(ad_set_id, ''), COALESCE(ad_id, '')
            )
            DO UPDATE SET
                value = official_metrics.value + EXCLUDED.value,
                extra = EXCLUDED.extra,
                updated_at = NOW()
        """)

        self.db.execute(sql, {
            "tenant_id": tenant_id,
            "provider": provider,
            "channel_slug": channel_slug,
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "metric_date": metric_date,
            "cost_type": cost_type,
            "extra": json.dumps(extra or {}),
            "campaign_id": campaign_id,
            "ad_set_id": ad_set_id,
            "ad_id": ad_id,
        })
        self.db.flush()

    def get_channel_metrics(
        self,
        tenant_id: UUID,
        provider: str,
        channel_slug: str,
        start_date: date,
        end_date: date,
    ) -> dict[str, float]:
        """Get aggregated metrics for a channel in a date range, using catalog semantics.

        - ADDITIVE: SUM across the date range
        - SNAPSHOT: value of the most recent date
        - NON_AGGREGABLE, WEIGHTED_AVERAGE, DERIVED: value of most recent date
          (cannot compute accurately without component data or API call)

        Returns: {"metric_name": aggregated_value, ...}
        """
        stmt = (
            select(
                OfficialMetricModel.metric_name,
                OfficialMetricModel.metric_date,
                OfficialMetricModel.value,
            )
            .where(
                OfficialMetricModel.tenant_id == tenant_id,
                OfficialMetricModel.provider == provider,
                OfficialMetricModel.channel_slug == channel_slug,
                OfficialMetricModel.metric_date.between(start_date, end_date),
            )
            .order_by(OfficialMetricModel.metric_name, OfficialMetricModel.metric_date)
        )
        rows = self.db.execute(stmt).all()

        # Group by metric name: {metric_name: [(date, value), ...]}
        grouped: dict[str, list[tuple]] = defaultdict(list)
        for row in rows:
            grouped[row.metric_name].append((row.metric_date, row.value))

        result: dict[str, float] = {}
        for metric_name, entries in grouped.items():
            defn = get_metric_def(metric_name)
            if defn is None or defn.aggregation == AggregationType.ADDITIVE:
                result[metric_name] = sum(v for _, v in entries)
            else:
                # SNAPSHOT, NON_AGGREGABLE, WEIGHTED_AVERAGE, DERIVED:
                # use most recent daily value as best approximation
                latest = max(entries, key=lambda x: x[0])
                result[metric_name] = float(latest[1])

        return result
