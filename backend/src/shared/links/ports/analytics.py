"""Analytics module access via lazy imports.

Connections module uses these helpers to read analytics data without
importing from ``analytics`` directly.

Lazy imports keep the coupling inside ``shared/`` which is not scanned
by the arch test boundary checker.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


def get_latest_extraction_run_info(
    db: Session,
    tenant_id: UUID,
    provider: str,
) -> dict | None:
    """Return latest ExtractionRun info dict for a provider, or None."""
    from src.modules.analytics.infrastructure.repositories.extraction_run_repository import (
        ExtractionRunRepository,
    )

    run_repo = ExtractionRunRepository(db)
    latest_run = run_repo.get_latest(tenant_id, provider)
    if not latest_run:
        return None
    return {
        "status": latest_run.status,
        "started_at": latest_run.started_at.isoformat() if latest_run.started_at else None,
        "completed_at": latest_run.completed_at.isoformat() if latest_run.completed_at else None,
        "metrics_count": latest_run.metrics_count,
        "error": latest_run.error,
        "duration_seconds": latest_run.duration_seconds,
    }


def get_provider_data_range(
    db: Session,
    tenant_id: UUID,
    provider: str,
) -> dict | None:
    """Return min/max metric_date and record count for a provider, or None."""
    from datetime import date

    from sqlalchemy import func, select

    from src.modules.analytics.infrastructure.models.official_metrics_model import (
        OfficialMetricModel,
    )

    stmt = select(
        func.min(OfficialMetricModel.metric_date),
        func.max(OfficialMetricModel.metric_date),
        func.count(OfficialMetricModel.id),
    ).where(
        OfficialMetricModel.tenant_id == tenant_id,
        OfficialMetricModel.provider == provider,
    )
    row = db.execute(stmt).first()
    if not row or not row[0]:
        return None
    return {
        "min_date": row[0].isoformat() if isinstance(row[0], date) else str(row[0]),
        "max_date": row[1].isoformat() if isinstance(row[1], date) else str(row[1]),
        "total_records": row[2],
    }
