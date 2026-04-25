"""WorkflowMetricModel — F9 quality KPIs per workflow per period.

# [COPILOT-WORKFLOW-METRIC-F9] -> docs/domains/copilot/redesign-2026-04/phases/F9-quality-observability.md

One row per ``(tenant_id, workflow_id, period_start)`` with rolling weekly
KPIs precomputed by the ARQ ``weekly_copilot_quality_eval`` task. The admin
``/copilot-quality`` page reads this table — it never invokes the LLM-judge
on page load (which would cost 50+ NANO calls per render).

Schema mirrors ``copilot_routing_log`` shape (per-tenant aggregate, no
foreign keys to keep tenant deletion simple). ``metadata`` JSONB carries
judge model name + response_id snapshot + per-dimension averages so
regressions are diagnosable without re-running the eval.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class WorkflowMetricModel(Base):
    """One row per ``(tenant_id, workflow_id, period_start)`` weekly bucket."""

    __tablename__ = "copilot_workflow_metric"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "workflow_id",
            "period_start",
            name="uq_workflow_metric_period",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    workflow_id = Column(String, nullable=False, index=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    started_count = Column(Integer, nullable=False, default=0)
    completed_count = Column(Integer, nullable=False, default=0)
    abandoned_count = Column(Integer, nullable=False, default=0)
    avg_turns_to_completion = Column(Float, nullable=True)
    accept_rate = Column(Numeric(4, 3), nullable=True)
    abandon_node = Column(String, nullable=True)
    judge_avg_score = Column(Numeric(4, 2), nullable=True)
    judge_sample_size = Column(Integer, nullable=False, default=0)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<WorkflowMetric workflow={self.workflow_id} tenant={self.tenant_id} period={self.period_start}>"
