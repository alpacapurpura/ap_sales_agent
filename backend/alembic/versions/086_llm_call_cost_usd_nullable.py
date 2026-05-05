"""llm_call_cost_usd_nullable — drop NOT NULL on cost_usd for cache-miss path.

PI-12 Sprint S1 · sales-agent-litellm-canonicalization · T-1.

T-1 (X2 ratificada) flips the runtime cost source from
:func:`calculate_cost` (computed locally over a snapshot) to
``kwargs["response_cost"]`` (LiteLLM-native, captured by
:class:`CostRecorderCustomLogger`). When the bridge misses (unknown model,
non-LiteLLM call, slow consumer past TTL), the recorder persists
``cost_usd = NULL`` so the audit row distinguishes "unknown" from a valid
``Decimal('0')``.

Schema impact: both ``copilot_llm_call.cost_usd`` and
``sales_agent_llm_call.cost_usd`` were declared ``NUMERIC(16,10) NOT NULL``
before T-1. This migration drops the NOT NULL constraint on both columns
idempotently — re-running the upgrade is a no-op.

Idempotent raw SQL per `.claude/rules/backend-migrations.md`.

Revision ID: 086_llm_call_cost_usd_nullable
Revises: 085_copilot_tenant_limits
Create Date: 2026-05-05
"""

from alembic import op

revision = "086_llm_call_cost_usd_nullable"
down_revision = "085_copilot_tenant_limits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Drop NOT NULL on copilot_llm_call.cost_usd and sales_agent_llm_call.cost_usd.

    ``ALTER COLUMN ... DROP NOT NULL`` is idempotent in Postgres — repeating
    the statement on an already-nullable column is a no-op (no error).
    """
    op.execute("ALTER TABLE copilot_llm_call ALTER COLUMN cost_usd DROP NOT NULL")
    op.execute("ALTER TABLE sales_agent_llm_call ALTER COLUMN cost_usd DROP NOT NULL")


def downgrade() -> None:
    """Restore NOT NULL — backfill any NULL rows with 0 first.

    The backfill uses ``WHERE cost_usd IS NULL`` so it is safe to run
    repeatedly. It loses no information: NULL post-T1 means "unknown
    cost", and the rollback explicitly chooses to coerce that to zero
    rather than leave the migration impossible to reverse.
    """
    op.execute("UPDATE copilot_llm_call SET cost_usd = 0 WHERE cost_usd IS NULL")
    op.execute("UPDATE sales_agent_llm_call SET cost_usd = 0 WHERE cost_usd IS NULL")
    op.execute("ALTER TABLE copilot_llm_call ALTER COLUMN cost_usd SET NOT NULL")
    op.execute("ALTER TABLE sales_agent_llm_call ALTER COLUMN cost_usd SET NOT NULL")
