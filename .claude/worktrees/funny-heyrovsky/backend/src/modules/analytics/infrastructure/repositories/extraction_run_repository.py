"""Repository for extraction_runs table — ETL run tracking.

Each extraction run records status, timing, and error information
for monitoring and retry logic.
"""

from datetime import datetime, timezone
from typing import List, Optional
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

    def create(self, tenant_id: UUID, provider: str) -> ExtractionRunModel:
        """Create a new extraction run with PENDING status."""
        run = ExtractionRunModel(
            tenant_id=tenant_id,
            provider=provider,
            status=ExtractionStatus.PENDING.value,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        self.db.flush()
        return run

    def update_status(
        self,
        run_id: UUID,
        status: ExtractionStatus,
        error: Optional[str] = None,
        metrics_count: int = 0,
        rows_extracted: int = 0,
        duration_seconds: Optional[float] = None,
        rate_limit_headroom: Optional[float] = None,
    ) -> ExtractionRunModel:
        """Update the status and metadata of an extraction run."""
        stmt = select(ExtractionRunModel).where(ExtractionRunModel.id == run_id)
        run = self.db.execute(stmt).scalars().first()

        if run is None:
            raise ValueError(f"ExtractionRun {run_id} not found")

        run.status = status.value
        run.error = error
        run.metrics_count = metrics_count
        run.rows_extracted = rows_extracted
        run.duration_seconds = duration_seconds
        run.rate_limit_headroom = rate_limit_headroom

        if status in (ExtractionStatus.SUCCESS, ExtractionStatus.FAILED):
            run.completed_at = datetime.now(timezone.utc)

        self.db.flush()
        return run

    def get_latest(
        self, tenant_id: UUID, provider: Optional[str] = None
    ) -> Optional[ExtractionRunModel]:
        """Get the latest extraction run for a tenant, optionally filtered by provider."""
        stmt = select(ExtractionRunModel).where(
            ExtractionRunModel.tenant_id == tenant_id
        )

        if provider is not None:
            stmt = stmt.where(ExtractionRunModel.provider == provider)

        stmt = stmt.order_by(ExtractionRunModel.created_at.desc()).limit(1)
        return self.db.execute(stmt).scalars().first()

    def get_failed(self, limit: int = 50) -> List[ExtractionRunModel]:
        """Get failed extraction runs for the retry queue."""
        stmt = (
            select(ExtractionRunModel)
            .where(ExtractionRunModel.status == ExtractionStatus.FAILED.value)
            .order_by(ExtractionRunModel.created_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
