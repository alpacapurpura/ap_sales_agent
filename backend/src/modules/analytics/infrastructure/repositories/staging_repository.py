"""Repository for staging_metrics table — raw ETL landing zone.

Staging data is temporary (30-day retention) and gets promoted
to official_metrics after transformation.
"""

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from luana_core_analytics_engine.infrastructure.models.staging_metrics_model import (
    StagingMetricModel,
)
from sqlalchemy import delete, select
from sqlalchemy.orm import Session


class StagingMetricsRepository:
    """CRUD operations for the staging_metrics table."""

    def __init__(self, db: Session) -> None:
        """Initialize staging metrics repository."""
        self.db = db

    def bulk_insert(self, metrics: list[StagingMetricModel]) -> int:
        """Bulk insert staging metrics. Returns the count inserted.

        Deduplicates by natural key before inserting to avoid
        UniqueViolation when a provider emits the same metric
        from multiple sub-extractors (e.g. account-level + campaign rollup).
        Last-wins semantics: if two rows share a key, the later one is kept.
        """
        if not metrics:
            return 0

        seen: dict[tuple, StagingMetricModel] = {}
        for m in metrics:
            key = (
                str(m.tenant_id),
                m.provider,
                m.channel_slug,
                m.metric_name,
                m.metric_date,
                m.campaign_id or "",
                m.ad_set_id or "",
                m.ad_id or "",
            )
            seen[key] = m

        deduped = list(seen.values())
        self.db.add_all(deduped)
        self.db.flush()
        return len(deduped)

    def get_by_run(self, extraction_run_id: UUID) -> list[StagingMetricModel]:
        """Get all staging metrics for a specific extraction run."""
        stmt = select(StagingMetricModel).where(
            StagingMetricModel.extraction_run_id == extraction_run_id,
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_by_tenant_provider_date(
        self,
        tenant_id: UUID,
        provider: str,
        start_date: date,
        end_date: date,
    ) -> list[StagingMetricModel]:
        """Get staging metrics filtered by tenant, provider, and date range."""
        stmt = select(StagingMetricModel).where(
            StagingMetricModel.tenant_id == tenant_id,
            StagingMetricModel.provider == provider,
            StagingMetricModel.metric_date >= start_date,
            StagingMetricModel.metric_date <= end_date,
        )
        return list(self.db.execute(stmt).scalars().all())

    def delete_by_tenant_provider(self, tenant_id: UUID, provider: str) -> int:
        """Delete all staging rows for a tenant+provider before re-inserting.

        Prevents UniqueViolation when re-running extraction for the same provider.
        """
        stmt = delete(StagingMetricModel).where(
            StagingMetricModel.tenant_id == tenant_id,
            StagingMetricModel.provider == provider,
        )
        result = self.db.execute(stmt)
        self.db.flush()
        return result.rowcount

    def delete_older_than(self, days: int = 30) -> int:
        """Delete staging rows older than N days (retention policy).

        Returns the number of rows deleted.
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        stmt = delete(StagingMetricModel).where(StagingMetricModel.created_at < cutoff)
        result = self.db.execute(stmt)
        self.db.flush()
        return result.rowcount
