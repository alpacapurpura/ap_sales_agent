"""SalesAgentWorkflowMetricModel — S10 quality KPIs por bucket por período.

# [SALES-AGENT-QUALITY-S10] -> docs/domains/sales-agent/redesign-2026-04/phases/S10-quality-eval-loop.md

Una fila por ``(tenant_id, bucket_id, period_start)`` weekly. ``bucket_id``
agrupa tipos de eval — categoría de golden (``qualification``,
``objections``, ``closing_payment``, ``booking``, ``multi_channel``,
``brand_voice_diff``) o stage del state machine (``rapport``,
``discovery``, ``presentation``, ``closing``).

Los goldens corren contra un sentinel tenant_id ``00000000-...`` (mismo
patrón que F11.5 RAG eval del copilot). El cron weekly puebla esta tabla;
el dashboard ``/sales-agent-quality`` lee precomputado — nunca invoca el
LLM-judge en render.

Schema mirror del ``copilot_workflow_metric`` (F9) con renombrado
``workflow_id → bucket_id`` para reflejar la semántica sales (no hay
"workflows" en sales_agent — hay categories + stages).
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


class SalesAgentWorkflowMetricModel(Base):
    """One row per ``(tenant_id, bucket_id, period_start)`` weekly bucket."""

    __tablename__ = "sales_agent_workflow_metric"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "bucket_id",
            "period_start",
            name="uq_sales_agent_workflow_metric_period",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    bucket_id = Column(String, nullable=False, index=True)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    started_count = Column(Integer, nullable=False, default=0)
    completed_count = Column(Integer, nullable=False, default=0)
    abandoned_count = Column(Integer, nullable=False, default=0)
    avg_turns_to_completion = Column(Float, nullable=True)
    judge_avg_score = Column(Numeric(4, 2), nullable=True)
    judge_sample_size = Column(Integer, nullable=False, default=0)
    extra_metadata = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<SalesAgentWorkflowMetric bucket={self.bucket_id} tenant={self.tenant_id} period={self.period_start}>"
