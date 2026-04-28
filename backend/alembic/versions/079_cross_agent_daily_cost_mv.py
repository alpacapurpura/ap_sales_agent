"""S2 — cross-agent daily LLM cost MV.

Adds ``mv_daily_llm_cost_per_tenant_v2`` — coarse rollup of every
agent's ``*_llm_call`` table, keyed by ``(agent_kind, tenant_id,
occurred_on)``. Backs the ``costo-agentes`` admin page; the legacy
per-agent ``mv_daily_llm_cost_per_tenant`` (migration 077) keeps its
finer model+provider+role breakdown for the existing copilot tab.

UNION ALL combines:

* ``copilot_llm_call``         (no ``lead_id``, has ``conversation_id``)
* ``sales_agent_llm_call``     (has ``lead_id``, no ``conversation_id``)

Common columns picked: ``tenant_id``, ``occurred_on`` (generated
column), ``cost_usd``, ``cost_tenant_currency``, ``tenant_currency``,
``turn_id``, ``status``. Per-agent specifics (lead_id, conversation_id)
are NOT in the MV — drilldowns stay against the underlying tables.

Refreshed hourly by ``aggregate_refresh_task`` (now refreshing both
MVs) using ``REFRESH MATERIALIZED VIEW CONCURRENTLY``. Concurrent
refresh requires a unique index — provided via
``ix_mv_daily_v2_pk(agent_kind, tenant_id, occurred_on)``. All three
columns are NOT NULL in the source UNION (literals + NOT NULL columns)
so the unique index never sees NULLs (which would otherwise break the
diff comparison Postgres uses during concurrent refresh).

Idempotent: ``DROP MATERIALIZED VIEW IF EXISTS`` + ``CREATE
MATERIALIZED VIEW IF NOT EXISTS``. Running ``alembic upgrade head``
twice in a row is a no-op.

Revision ID: 079_cross_agent_daily_cost_mv
Revises: 078_sales_agent_observability_tables
Create Date: 2026-04-28 04:00:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "079_cross_agent_daily_cost_mv"
down_revision: str | None = "078_sales_agent_observability_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the cross-agent daily-cost MV + unique index. Idempotent."""
    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_llm_cost_per_tenant_v2 AS
        SELECT
            'copilot'::VARCHAR(32) AS agent_kind,
            tenant_id,
            occurred_on,
            COUNT(*)                                  AS call_count,
            COUNT(DISTINCT turn_id)                   AS turn_count,
            SUM(cost_usd)                             AS cost_usd,
            SUM(cost_tenant_currency)                 AS cost_tenant_currency,
            MAX(tenant_currency)                      AS tenant_currency,
            COUNT(*) FILTER (WHERE status = 'error')  AS error_count
        FROM copilot_llm_call
        GROUP BY tenant_id, occurred_on
        UNION ALL
        SELECT
            'sales_agent'::VARCHAR(32),
            tenant_id,
            occurred_on,
            COUNT(*),
            COUNT(DISTINCT turn_id),
            SUM(cost_usd),
            SUM(cost_tenant_currency),
            MAX(tenant_currency),
            COUNT(*) FILTER (WHERE status = 'error')
        FROM sales_agent_llm_call
        GROUP BY tenant_id, occurred_on
        """,
    )
    # CONCURRENT refresh requires a UNIQUE index covering every
    # discriminator. agent_kind / tenant_id / occurred_on are all NOT
    # NULL in the UNION above so this index never holds a NULL row.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_daily_v2_pk
        ON mv_daily_llm_cost_per_tenant_v2 (agent_kind, tenant_id, occurred_on)
        """,
    )


def downgrade() -> None:
    """Drop the MV. Idempotent."""
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_daily_llm_cost_per_tenant_v2 CASCADE")
