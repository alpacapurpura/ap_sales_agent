"""sales_agent: +sales_agent_workflow_metric table (S10)

Revision ID: 082_sales_agent_workflow_metric
Revises: 081_sales_agent_payment_lifecycle
Create Date: 2026-04-28

S10 deliverable §criterio 4. Una fila por ``(tenant_id, bucket_id,
period_start)`` weekly bucket con KPIs de calidad precomputados (started,
judge_avg_score, sample_size, avg_turns). Alimenta el dashboard
``/sales-agent-quality`` admin.

Mirror semántico del ``copilot_workflow_metric`` (072) con renombrado
``workflow_id → bucket_id`` para reflejar que sales_agent agrupa por
golden category | stage del state machine, no por workflow.

Idempotente (raw ``CREATE TABLE IF NOT EXISTS`` + indexes) per
.claude/rules/backend-migrations.md.

refs:
- docs/domains/sales-agent/redesign-2026-04/phases/S10-quality-eval-loop.md
- backend/src/modules/sales_agent/infrastructure/models/workflow_metric_model.py
"""

from collections.abc import Sequence

from alembic import op

revision: str = "082_sales_agent_workflow_metric"
down_revision: str | None = "081_sales_agent_payment_lifecycle"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create ``sales_agent_workflow_metric`` (idempotent)."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sales_agent_workflow_metric (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            bucket_id TEXT NOT NULL,
            period_start TIMESTAMPTZ NOT NULL,
            period_end TIMESTAMPTZ NOT NULL,
            started_count INTEGER NOT NULL DEFAULT 0,
            completed_count INTEGER NOT NULL DEFAULT 0,
            abandoned_count INTEGER NOT NULL DEFAULT 0,
            avg_turns_to_completion DOUBLE PRECISION NULL,
            judge_avg_score NUMERIC(4, 2) NULL,
            judge_sample_size INTEGER NOT NULL DEFAULT 0,
            extra_metadata JSONB NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_sales_agent_workflow_metric_period
        ON sales_agent_workflow_metric (tenant_id, bucket_id, period_start)
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sales_agent_workflow_metric_tenant_period
        ON sales_agent_workflow_metric (tenant_id, period_start DESC)
        """,
    )


def downgrade() -> None:
    """Explicit NO-OP — KPI history is observational, never dropped."""
