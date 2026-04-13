"""Promotes ManyChat staging metrics to official metrics.

Called after webhook ingestion to make metrics available to the dashboard.
Uses the same transform + upsert pattern as the ETL pipeline but optimized
for single-event insertion (no full extraction run needed).
"""

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.analytics.application.cost_type_mapping import get_cost_type
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)


class ManyChatMetricsPromoter:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.official_repo = OfficialMetricsRepository(db)

    def promote_event(
        self,
        tenant_id: UUID,
        channel_slug: str,
        metric_name: str,
        metric_date: date,
        stage_slug: str,
        value: float = 1.0,
        extra: dict | None = None,
    ) -> None:
        """Upsert a single metric event into official_metrics.

        Uses SUM aggregation: if a row for (tenant, provider, channel, metric, date)
        already exists, adds `value` to the current value.
        """
        cost_type = get_cost_type(channel_slug, stage_slug)

        self.official_repo.upsert_increment(
            tenant_id=tenant_id,
            provider="manychat",
            channel_slug=channel_slug,
            metric_name=metric_name,
            value=value,
            unit="count",
            metric_date=metric_date,
            cost_type=cost_type.value if cost_type and hasattr(cost_type, "value") else cost_type,
            extra=extra or {},
        )
