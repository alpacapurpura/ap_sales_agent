"""SalesAgentWorkflowMetricRepository — S10 KPI upsert.

# [SALES-AGENT-QUALITY-S10] -> docs/domains/sales-agent/redesign-2026-04/phases/S10-quality-eval-loop.md

Mirror del :class:`src.modules.copilot.infrastructure.repositories.workflow_metric_repository.WorkflowMetricRepository`
con bucket_id en lugar de workflow_id (semántica sales: category | stage).
Sync repo invocado desde el ARQ weekly task. Idempotente vía
``ON CONFLICT (tenant_id, bucket_id, period_start) DO UPDATE``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from luana_core_sales_agent.infrastructure.models.workflow_metric_model import (
    SalesAgentWorkflowMetricModel,
)
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@dataclass(frozen=True, slots=True)
class SalesAgentWorkflowMetricRow:
    """Read-side DTO returned by the repo."""

    tenant_id: UUID
    bucket_id: str
    period_start: datetime
    period_end: datetime
    started_count: int
    completed_count: int
    abandoned_count: int
    avg_turns_to_completion: float | None
    judge_avg_score: float | None
    judge_sample_size: int
    extra_metadata: dict[str, Any] | None


class SalesAgentWorkflowMetricRepository:
    """Upsert + read of sales_agent KPI rows."""

    def __init__(self, db: Session) -> None:
        """Bind the repo to an open SQLAlchemy session."""
        self._db = db

    def upsert(
        self,
        *,
        tenant_id: UUID,
        bucket_id: str,
        period_start: datetime,
        period_end: datetime,
        started_count: int,
        completed_count: int = 0,
        abandoned_count: int = 0,
        avg_turns_to_completion: float | None = None,
        judge_avg_score: float | None = None,
        judge_sample_size: int = 0,
        extra_metadata: dict[str, Any] | None = None,
    ) -> None:
        """Insert or update the metric row for the given period bucket."""
        stmt = pg_insert(SalesAgentWorkflowMetricModel).values(
            tenant_id=tenant_id,
            bucket_id=bucket_id,
            period_start=period_start,
            period_end=period_end,
            started_count=started_count,
            completed_count=completed_count,
            abandoned_count=abandoned_count,
            avg_turns_to_completion=avg_turns_to_completion,
            judge_avg_score=judge_avg_score,
            judge_sample_size=judge_sample_size,
            extra_metadata=extra_metadata,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["tenant_id", "bucket_id", "period_start"],
            set_={
                "period_end": stmt.excluded.period_end,
                "started_count": stmt.excluded.started_count,
                "completed_count": stmt.excluded.completed_count,
                "abandoned_count": stmt.excluded.abandoned_count,
                "avg_turns_to_completion": stmt.excluded.avg_turns_to_completion,
                "judge_avg_score": stmt.excluded.judge_avg_score,
                "judge_sample_size": stmt.excluded.judge_sample_size,
                "extra_metadata": stmt.excluded.extra_metadata,
            },
        )
        self._db.execute(stmt)
        self._db.commit()

    def list_for_tenant(
        self,
        *,
        tenant_id: UUID,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[SalesAgentWorkflowMetricRow]:
        """Return tenant rows ordered by ``period_start DESC``."""
        stmt = (
            select(SalesAgentWorkflowMetricModel)
            .where(SalesAgentWorkflowMetricModel.tenant_id == tenant_id)
            .order_by(SalesAgentWorkflowMetricModel.period_start.desc())
            .limit(limit)
        )
        if since is not None:
            stmt = stmt.where(SalesAgentWorkflowMetricModel.period_start >= since)
        rows = self._db.execute(stmt).scalars().all()
        return [
            SalesAgentWorkflowMetricRow(
                tenant_id=row.tenant_id,
                bucket_id=row.bucket_id,
                period_start=row.period_start,
                period_end=row.period_end,
                started_count=row.started_count,
                completed_count=row.completed_count,
                abandoned_count=row.abandoned_count,
                avg_turns_to_completion=row.avg_turns_to_completion,
                judge_avg_score=(float(row.judge_avg_score) if row.judge_avg_score is not None else None),
                judge_sample_size=row.judge_sample_size,
                extra_metadata=row.extra_metadata,
            )
            for row in rows
        ]


__all__ = (
    "SalesAgentWorkflowMetricRepository",
    "SalesAgentWorkflowMetricRow",
)
