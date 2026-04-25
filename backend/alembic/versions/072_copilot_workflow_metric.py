"""copilot: +copilot_workflow_metric table (F9)

Revision ID: 072_copilot_workflow_metric
Revises: 071_copilot_workflow_state
Create Date: 2026-04-25

F9 deliverable §4.4. One row per ``(tenant_id, workflow_id, period_start)``
weekly bucket — feeds the ``/copilot-quality`` admin dashboard with
precomputed completion / accept / judge-score KPIs.

Migration is idempotent (raw ``CREATE TABLE IF NOT EXISTS`` + ``CREATE
INDEX IF NOT EXISTS`` + ``ADD CONSTRAINT IF NOT EXISTS`` per
.claude/rules/backend-migrations.md).

refs:
- docs/domains/copilot/redesign-2026-04/phases/F9-quality-observability.md
- backend/src/modules/copilot/infrastructure/models/workflow_metric_model.py
"""

from collections.abc import Sequence

from alembic import op

revision: str = "072_copilot_workflow_metric"
down_revision: str | None = "071_copilot_workflow_state"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create ``copilot_workflow_metric`` (idempotent)."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS copilot_workflow_metric (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            workflow_id TEXT NOT NULL,
            period_start TIMESTAMPTZ NOT NULL,
            period_end TIMESTAMPTZ NOT NULL,
            started_count INTEGER NOT NULL DEFAULT 0,
            completed_count INTEGER NOT NULL DEFAULT 0,
            abandoned_count INTEGER NOT NULL DEFAULT 0,
            avg_turns_to_completion DOUBLE PRECISION NULL,
            accept_rate NUMERIC(4, 3) NULL,
            abandon_node TEXT NULL,
            judge_avg_score NUMERIC(4, 2) NULL,
            judge_sample_size INTEGER NOT NULL DEFAULT 0,
            extra_metadata JSONB NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_workflow_metric_period
        ON copilot_workflow_metric (tenant_id, workflow_id, period_start)
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_workflow_metric_tenant_period
        ON copilot_workflow_metric (tenant_id, period_start DESC)
        """,
    )


def downgrade() -> None:
    """Explicit NO-OP — KPI history is observational data, never dropped."""
