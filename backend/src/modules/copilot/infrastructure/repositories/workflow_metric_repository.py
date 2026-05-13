"""WorkflowMetricRepository — F9 KPI upsert per (tenant, workflow, period).

# [COPILOT-WORKFLOW-METRIC-F9]

Sync repo — invoked from the ARQ weekly task (sync inside ``async def`` is
fine; the task already opens its own ``SessionLocal``). Mirrors the F4
``CopilotInspirationRepository`` pattern: tenant-scoped queries, idempotent
upsert on the natural key, no business logic in the repo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from luana_core_copilot.infrastructure.models.workflow_metric_model import (
    WorkflowMetricModel,
)
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@dataclass(frozen=True, slots=True)
class WorkflowMetricRow:
    """Read-side DTO returned by the repo."""

    tenant_id: UUID
    workflow_id: str
    period_start: datetime
    period_end: datetime
    started_count: int
    completed_count: int
    abandoned_count: int
    avg_turns_to_completion: float | None
    accept_rate: float | None
    abandon_node: str | None
    judge_avg_score: float | None
    judge_sample_size: int
    extra_metadata: dict[str, Any] | None


class WorkflowMetricRepository:
    """Upsert + read of workflow KPI rows."""

    def __init__(self, db: Session) -> None:
        """Bind the repo to an open SQLAlchemy session."""
        self._db = db

    def upsert(
        self,
        *,
        tenant_id: UUID,
        workflow_id: str,
        period_start: datetime,
        period_end: datetime,
        started_count: int,
        completed_count: int,
        abandoned_count: int,
        avg_turns_to_completion: float | None = None,
        accept_rate: float | None = None,
        abandon_node: str | None = None,
        judge_avg_score: float | None = None,
        judge_sample_size: int = 0,
        extra_metadata: dict[str, Any] | None = None,
    ) -> None:
        """Insert or update the metric row for the given period bucket.

        Uses ``index_elements`` (not ``constraint=``) to keep the SQL
        portable across SQLite (tests) and Postgres (prod) — pattern
        documented in F2/F3 learnings.
        """
        stmt = pg_insert(WorkflowMetricModel).values(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            period_start=period_start,
            period_end=period_end,
            started_count=started_count,
            completed_count=completed_count,
            abandoned_count=abandoned_count,
            avg_turns_to_completion=avg_turns_to_completion,
            accept_rate=accept_rate,
            abandon_node=abandon_node,
            judge_avg_score=judge_avg_score,
            judge_sample_size=judge_sample_size,
            extra_metadata=extra_metadata,
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["tenant_id", "workflow_id", "period_start"],
            set_={
                "period_end": stmt.excluded.period_end,
                "started_count": stmt.excluded.started_count,
                "completed_count": stmt.excluded.completed_count,
                "abandoned_count": stmt.excluded.abandoned_count,
                "avg_turns_to_completion": stmt.excluded.avg_turns_to_completion,
                "accept_rate": stmt.excluded.accept_rate,
                "abandon_node": stmt.excluded.abandon_node,
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
    ) -> list[WorkflowMetricRow]:
        """Return tenant rows ordered by ``period_start DESC``."""
        stmt = (
            select(WorkflowMetricModel)
            .where(WorkflowMetricModel.tenant_id == tenant_id)
            .order_by(WorkflowMetricModel.period_start.desc())
            .limit(limit)
        )
        if since is not None:
            stmt = stmt.where(WorkflowMetricModel.period_start >= since)
        rows = self._db.execute(stmt).scalars().all()
        return [
            WorkflowMetricRow(
                tenant_id=row.tenant_id,
                workflow_id=row.workflow_id,
                period_start=row.period_start,
                period_end=row.period_end,
                started_count=row.started_count,
                completed_count=row.completed_count,
                abandoned_count=row.abandoned_count,
                avg_turns_to_completion=row.avg_turns_to_completion,
                accept_rate=float(row.accept_rate) if row.accept_rate is not None else None,
                abandon_node=row.abandon_node,
                judge_avg_score=(float(row.judge_avg_score) if row.judge_avg_score is not None else None),
                judge_sample_size=row.judge_sample_size,
                extra_metadata=row.extra_metadata,
            )
            for row in rows
        ]


__all__ = ("WorkflowMetricRepository", "WorkflowMetricRow")
