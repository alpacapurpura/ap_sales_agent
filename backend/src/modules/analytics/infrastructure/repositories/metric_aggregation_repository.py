"""Repository for metric_aggregations table — idempotent replace pattern.

Uses DELETE + INSERT within the caller's transaction to avoid
UniqueViolation on re-runs. This mirrors the staging repo pattern.
"""

import uuid
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

# Model import is needed to ensure SQLAlchemy mapper registration
from src.modules.analytics.infrastructure.models.metric_aggregation_model import (  # noqa: F401
    MetricAggregationModel,
)


class MetricAggregationRepository:
    """CRUD operations for the metric_aggregations table."""

    def __init__(self, db: Session):
        self.db = db

    _DELETE_SCOPE_SQL = text("""
        DELETE FROM metric_aggregations
        WHERE tenant_id = :tenant_id
          AND channel_slug = :channel_slug
    """)

    _INSERT_SQL = text("""
        INSERT INTO metric_aggregations (
            id, tenant_id, channel_slug, metric_name,
            period_type, period_start, period_end,
            value, unit, currency, cost_type,
            extraction_run_id, computed_at
        ) VALUES (
            :id, :tenant_id, :channel_slug, :metric_name,
            :period_type, :period_start, :period_end,
            :value, :unit, :currency, :cost_type,
            :extraction_run_id, NOW()
        )
    """)

    def replace_aggregations(
        self,
        tenant_id: UUID,
        channel_slug: str,
        agg_dicts: list[dict],
    ) -> int:
        """Replace all aggregations for a tenant+channel scope.

        Deletes existing rows, then inserts new ones within the
        caller's transaction. This makes re-runs idempotent.

        Returns the number of rows inserted.
        """
        if not agg_dicts:
            return 0

        # Step 1: Delete existing aggregations for this scope
        self.db.execute(
            self._DELETE_SCOPE_SQL,
            {"tenant_id": str(tenant_id), "channel_slug": channel_slug},
        )

        # Step 2: Insert new aggregations
        for agg in agg_dicts:
            self.db.execute(
                self._INSERT_SQL,
                {
                    "id": str(uuid.uuid4()),
                    "tenant_id": str(agg["tenant_id"]),
                    "channel_slug": agg["channel_slug"],
                    "metric_name": agg["metric_name"],
                    "period_type": agg["period_type"],
                    "period_start": agg["period_start"],
                    "period_end": agg["period_end"],
                    "value": agg["value"],
                    "unit": agg["unit"],
                    "currency": agg.get("currency"),
                    "cost_type": agg.get("cost_type"),
                    "extraction_run_id": str(agg["extraction_run_id"])
                    if agg.get("extraction_run_id")
                    else None,
                },
            )

        self.db.flush()
        return len(agg_dicts)
