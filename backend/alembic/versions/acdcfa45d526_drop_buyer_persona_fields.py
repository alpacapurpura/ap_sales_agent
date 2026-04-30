"""drop_buyer_persona_fields

Drops ``objections`` + ``preferred_channels`` JSONB columns from
buyer_personas. Both fields were verified unused by downstream consumers
(sales_agent.objection_history is session-state distinct; offer.objections
is a different module's field). Form-runtime CRUD users may have populated
data; the cleanup intentionally accepts data loss (decision PI-4 S1 PR-1,
approved by Chris 2026-04-29 — can_propose=False + no downstream consumer).

Downgrade re-creates the columns empty — data populated before upgrade
is NOT recovered (DROP COLUMN is irreversible). Documented intentionally.

Revision ID: acdcfa45d526
Revises: 082_sales_agent_workflow_metric
Create Date: 2026-04-29 20:52:33.856718

"""

from collections.abc import Sequence

from alembic import op

revision: str = "acdcfa45d526"
down_revision: str | None = "082_sales_agent_workflow_metric"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop objections and preferred_channels from buyer_personas."""
    op.execute("ALTER TABLE buyer_personas DROP COLUMN IF EXISTS objections")
    op.execute("ALTER TABLE buyer_personas DROP COLUMN IF EXISTS preferred_channels")


def downgrade() -> None:
    """Restore columns (data from before upgrade is not recovered)."""
    op.execute("ALTER TABLE buyer_personas ADD COLUMN IF NOT EXISTS objections JSONB NOT NULL DEFAULT '[]'")
    op.execute("ALTER TABLE buyer_personas ADD COLUMN IF NOT EXISTS preferred_channels JSONB NOT NULL DEFAULT '[]'")
