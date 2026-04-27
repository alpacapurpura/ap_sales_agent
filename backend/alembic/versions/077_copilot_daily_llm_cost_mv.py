"""Phase 3 — daily LLM cost materialised view per tenant.

Adds ``mv_daily_llm_cost_per_tenant`` — pre-aggregated rollup of
``copilot_llm_call`` by ``(tenant_id, day, model, provider, role)`` so
the costo-copilot dashboard answers `tenants_summary` and `tenant_detail`
in <200ms even when the underlying table grows past 1M rows.

Refreshed hourly by ``aggregate_refresh_task`` (T3.4) using
``REFRESH MATERIALIZED VIEW CONCURRENTLY``, which requires the unique
index over the group-by tuple. Concurrent refresh keeps the dashboard
read path unblocked during refresh.

Idempotent: ``CREATE MATERIALIZED VIEW IF NOT EXISTS`` + ``DROP
MATERIALIZED VIEW IF EXISTS`` for the downgrade.

Schema source of truth: ``docs/domains/copilot/observability-rebuild-2026-04
/ARCHITECTURE.md`` §4.3.

Revision ID: 077_copilot_daily_llm_cost_mv
Revises: 076_copilot_billing_cycle_function
Create Date: 2026-04-27 06:30:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "077_copilot_daily_llm_cost_mv"
down_revision: str | None = "076_copilot_billing_cycle_function"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the daily-cost MV + unique index. Idempotent."""
    op.execute(
        """
        CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_llm_cost_per_tenant AS
        SELECT
            tenant_id,
            occurred_on,
            model_responded,
            provider,
            role,
            COUNT(*) AS call_count,
            COUNT(DISTINCT turn_id) AS turn_count,
            COUNT(DISTINCT conversation_id) AS conversation_count,
            SUM(input_tokens) AS input_tokens,
            SUM(output_tokens) AS output_tokens,
            SUM(cached_read_tokens) AS cached_read_tokens,
            SUM(cost_usd) AS cost_usd,
            SUM(cost_tenant_currency) AS cost_tenant_currency,
            AVG(duration_ms)::INT AS avg_duration_ms,
            COUNT(*) FILTER (WHERE status = 'error') AS error_count,
            MAX(tenant_currency) AS tenant_currency
        FROM copilot_llm_call
        GROUP BY tenant_id, occurred_on, model_responded, provider, role
        """,
    )
    # CONCURRENT refresh requires a UNIQUE index covering every group-by
    # column. Naming follows the table convention so the same lookup
    # paths used by hand queries hit the index.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_mv_daily_llm_cost_per_tenant_pk
        ON mv_daily_llm_cost_per_tenant
            (tenant_id, occurred_on, model_responded, provider, role)
        """,
    )


def downgrade() -> None:
    """Drop the MV. Idempotent."""
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_daily_llm_cost_per_tenant CASCADE")
