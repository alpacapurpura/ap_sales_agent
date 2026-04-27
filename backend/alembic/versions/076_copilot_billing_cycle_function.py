"""Phase 3 — billing cycle SQL function.

Adds ``compute_cycle_start(p_tenant UUID, p_date DATE) RETURNS DATE`` —
the canonical Postgres-side helper that maps an arbitrary date to the
first day of the billing cycle it belongs to, honouring the per-tenant
``billing_cycle_anchor_day`` from ``tenant_billing_config`` (default
25).

Idempotent: ``CREATE OR REPLACE FUNCTION`` overwrites in place.
``DROP FUNCTION IF EXISTS`` covers the downgrade.

Why a SQL function instead of relying on the Python helper? Group-by
queries over ``copilot_llm_call`` need the cycle key inside SQL —
streaming millions of rows back to Python just to bucket them defeats
the materialised view. The Python helper
(:func:`src.modules.copilot.observability.reporting.cycle_window.compute_cycle_start_py`)
is the single source of truth for the *shape* of the math; the SQL
function mirrors it for queries.

Schema source of truth: ``docs/domains/copilot/observability-rebuild-2026-04
/ARCHITECTURE.md`` §4.4.

Revision ID: 076_copilot_billing_cycle_function
Revises: 075_copilot_observability_rebuild
Create Date: 2026-04-27 06:00:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "076_copilot_billing_cycle_function"
down_revision: str | None = "075_copilot_observability_rebuild"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create ``compute_cycle_start`` SQL function. Idempotent."""
    op.execute(
        """
        CREATE OR REPLACE FUNCTION compute_cycle_start(p_tenant UUID, p_date DATE)
        RETURNS DATE
        LANGUAGE plpgsql
        IMMUTABLE
        AS $$
        DECLARE
            anchor SMALLINT;
            safe_anchor SMALLINT;
            month_last_day SMALLINT;
            cycle_year INT;
            cycle_month INT;
        BEGIN
            -- Resolve the anchor: tenant override or default 25.
            SELECT billing_cycle_anchor_day
              INTO anchor
              FROM tenant_billing_config
             WHERE tenant_id = p_tenant;
            IF anchor IS NULL THEN
                anchor := 25;
            END IF;

            -- Clamp to the last day of the current month (handles Feb).
            month_last_day := EXTRACT(DAY FROM
                (date_trunc('month', p_date) + INTERVAL '1 month' - INTERVAL '1 day')
            )::SMALLINT;
            safe_anchor := LEAST(anchor, month_last_day);

            IF EXTRACT(DAY FROM p_date)::SMALLINT >= safe_anchor THEN
                RETURN make_date(
                    EXTRACT(YEAR  FROM p_date)::INT,
                    EXTRACT(MONTH FROM p_date)::INT,
                    safe_anchor
                );
            END IF;

            -- Otherwise roll back to the anchor in the previous month.
            cycle_year  := EXTRACT(YEAR  FROM (p_date - INTERVAL '1 month'))::INT;
            cycle_month := EXTRACT(MONTH FROM (p_date - INTERVAL '1 month'))::INT;
            month_last_day := EXTRACT(DAY FROM (
                date_trunc('month', make_date(cycle_year, cycle_month, 1))
                + INTERVAL '1 month' - INTERVAL '1 day'
            ))::SMALLINT;
            safe_anchor := LEAST(anchor, month_last_day);
            RETURN make_date(cycle_year, cycle_month, safe_anchor);
        END
        $$
        """,
    )


def downgrade() -> None:
    """Drop the SQL function. Idempotent."""
    op.execute("DROP FUNCTION IF EXISTS compute_cycle_start(UUID, DATE)")
