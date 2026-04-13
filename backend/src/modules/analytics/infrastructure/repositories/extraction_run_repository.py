"""Repository for extraction_runs table — ETL run tracking.

Each extraction run records status, timing, and error information
for monitoring and retry logic.
"""

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.analytics.domain.enums import ExtractionStatus
from src.modules.analytics.infrastructure.models.extraction_run_model import (
    ExtractionRunModel,
)


class ExtractionRunRepository:
    """CRUD operations for the extraction_runs table."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        tenant_id: UUID,
        provider: str,
        period_start: date | None = None,
        period_end: date | None = None,
        extraction_type: str | None = None,
    ) -> ExtractionRunModel:
        """Create a new extraction run with PENDING status.

        Args:
            tenant_id: Tenant owning the run (required for isolation).
            provider: Provider identifier (``meta``, ``shopify``, etc.).
            period_start: First calendar day covered by this extraction.
                Populated so ops can audit what date range the run actually
                loaded. Kept optional for backwards compatibility with
                legacy callers that haven't been updated yet.
            period_end: Last calendar day covered by this extraction.
            extraction_type: ``scheduled`` (cron), ``initial_load`` (first
                sync after a connect), or ``period`` (period_pipeline for
                NON_AGGREGABLE metrics). Falls back to the model's server
                default when omitted.
        """
        kwargs: dict = {
            "tenant_id": tenant_id,
            "provider": provider,
            "status": ExtractionStatus.PENDING.value,
            "started_at": datetime.now(UTC),
            "period_start": period_start,
            "period_end": period_end,
        }
        if extraction_type is not None:
            kwargs["extraction_type"] = extraction_type
        run = ExtractionRunModel(**kwargs)
        self.db.add(run)
        self.db.flush()
        return run

    def update_status(
        self,
        run_id: UUID,
        status: ExtractionStatus,
        error: str | None = None,
        metrics_count: int = 0,
        rows_extracted: int = 0,
        duration_seconds: float | None = None,
        rate_limit_headroom: float | None = None,
        sub_extractor_failures: list | None = None,
    ) -> ExtractionRunModel:
        """Update the status and metadata of an extraction run."""
        stmt = select(ExtractionRunModel).where(ExtractionRunModel.id == run_id)
        run = self.db.execute(stmt).scalars().first()

        if run is None:
            msg = f"ExtractionRun {run_id} not found"
            raise ValueError(msg)

        run.status = status.value
        run.error = error
        run.metrics_count = metrics_count
        run.rows_extracted = rows_extracted
        run.duration_seconds = duration_seconds
        run.rate_limit_headroom = rate_limit_headroom
        run.sub_extractor_failures = sub_extractor_failures or []

        if status in (
            ExtractionStatus.SUCCESS,
            ExtractionStatus.FAILED,
            ExtractionStatus.PARTIAL_SUCCESS,
        ):
            run.completed_at = datetime.now(UTC)

        self.db.flush()
        return run

    def get_latest(
        self, tenant_id: UUID, provider: str | None = None
    ) -> ExtractionRunModel | None:
        """Get the latest extraction run for a tenant, optionally filtered by provider."""
        stmt = select(ExtractionRunModel).where(
            ExtractionRunModel.tenant_id == tenant_id
        )

        if provider is not None:
            stmt = stmt.where(ExtractionRunModel.provider == provider)

        stmt = stmt.order_by(ExtractionRunModel.created_at.desc()).limit(1)
        return self.db.execute(stmt).scalars().first()

    def get_failed(self, limit: int = 50) -> list[ExtractionRunModel]:
        """Get failed extraction runs for the retry queue."""
        stmt = (
            select(ExtractionRunModel)
            .where(ExtractionRunModel.status == ExtractionStatus.FAILED.value)
            .order_by(ExtractionRunModel.created_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
