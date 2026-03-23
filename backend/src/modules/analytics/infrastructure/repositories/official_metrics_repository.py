"""Repository for official_metrics table — validated dashboard data.

Official metrics are the source of truth for dashboard queries.
They are promoted from staging_metrics after transformation.
"""

import uuid
from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.modules.analytics.infrastructure.models.official_metrics_model import (
    OfficialMetricModel,
)


class OfficialMetricsRepository:
    """CRUD operations for the official_metrics table."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_from_staging(self, metrics: List[dict]) -> int:
        """Insert or update official metrics from transformed staging data.

        Uses PostgreSQL ON CONFLICT DO UPDATE on the composite key
        (tenant_id, provider, channel_slug, metric_name, metric_date,
         campaign_id, ad_set_id, ad_id) to deduplicate.

        Returns the number of rows upserted.
        """
        if not metrics:
            return 0

        count = 0
        for metric_data in metrics:
            # Ensure id is set
            if "id" not in metric_data:
                metric_data["id"] = uuid.uuid4()

            stmt = pg_insert(OfficialMetricModel).values(**metric_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=[
                    "tenant_id",
                    "provider",
                    "channel_slug",
                    "metric_name",
                    "metric_date",
                ],
                set_={
                    "value": stmt.excluded.value,
                    "unit": stmt.excluded.unit,
                    "currency": stmt.excluded.currency,
                    "spend": stmt.excluded.spend,
                    "revenue": stmt.excluded.revenue,
                    "cost_type": stmt.excluded.cost_type,
                    "extra": stmt.excluded.extra,
                    "source_extraction_run_id": stmt.excluded.source_extraction_run_id,
                },
            )
            self.db.execute(stmt)
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
