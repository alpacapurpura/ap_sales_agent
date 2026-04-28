"""Sales-agent observability tables — event-sourced parity with copilot.

S1 of the sales-agent redesign 2026-04 (see
``docs/domains/sales-agent/redesign-2026-04/phases/S1-sales-agent-observability-parity.md``).

Mirrors the ``copilot_*`` observability schema (migrations 075 + 059 +
20260421_1200) and adds two sales-agent-specific columns:

* ``lead_id``       — UUID of the CRM lead the conversation belongs to.
                      Mandatory; every sales turn is anchored to a lead.
* ``channel_type``  — VARCHAR(32) — telegram | whatsapp | instagram | web.

Three new tables:

* ``sales_agent_llm_call``     — one immutable row per LLM invocation,
  carrying token counts, snapshot pricing, status. Backs billing /
  per-tenant cost dashboards (S2).
* ``sales_agent_trace_event``  — turn timeline rows (turn_start,
  turn_end, llm_call mirror, tool_call, node_enter/exit, error,
  domain_event).
* ``sales_agent_routing_log``  — tier + stage + lead_score per turn.
  Used by S4 ``sales-routing`` admin page.

Reference data (``model_pricing_snapshot`` + ``tenant_billing_config``)
is **not** duplicated — both are global cross-agent and live in the
shared schema (migration 075).

Idempotent: every statement uses ``IF NOT EXISTS``. Re-running
``alembic upgrade head`` is a no-op.

Revision ID: 078_sales_agent_observability_tables
Revises: 077_copilot_daily_llm_cost_mv
Create Date: 2026-04-28 00:00:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "078_sales_agent_observability_tables"
down_revision: str | None = "077_copilot_daily_llm_cost_mv"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the three sales-agent observability tables. Idempotent."""
    # ── sales_agent_llm_call ─────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sales_agent_llm_call (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            lead_id UUID NOT NULL,
            channel_type VARCHAR(32) NOT NULL,
            turn_id UUID NOT NULL,
            span_id UUID NOT NULL,
            parent_span_id UUID,
            role VARCHAR(32) NOT NULL,
            provider VARCHAR(32) NOT NULL,
            model_requested VARCHAR(128) NOT NULL,
            model_responded VARCHAR(128) NOT NULL,
            input_tokens INTEGER NOT NULL DEFAULT 0,
            output_tokens INTEGER NOT NULL DEFAULT 0,
            cached_read_tokens INTEGER NOT NULL DEFAULT 0,
            cached_write_tokens INTEGER NOT NULL DEFAULT 0,
            reasoning_tokens INTEGER NOT NULL DEFAULT 0,
            pricing_version_id UUID NOT NULL,
            input_unit_cost_usd NUMERIC(14,12) NOT NULL,
            output_unit_cost_usd NUMERIC(14,12) NOT NULL,
            cached_read_unit_cost_usd NUMERIC(14,12) NOT NULL DEFAULT 0,
            cost_usd NUMERIC(16,10) NOT NULL,
            tenant_currency CHAR(3),
            fx_rate_to_tenant NUMERIC(16,8),
            fx_rate_source VARCHAR(32),
            cost_tenant_currency NUMERIC(16,8),
            started_at TIMESTAMPTZ NOT NULL,
            duration_ms INTEGER NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'ok',
            error_type VARCHAR(64),
            occurred_on DATE GENERATED ALWAYS AS ((started_at AT TIME ZONE 'UTC')::date) STORED,
            occurred_year_month VARCHAR(7) GENERATED ALWAYS AS (
                EXTRACT(YEAR FROM started_at AT TIME ZONE 'UTC')::INT::TEXT
                || '-'
                || LPAD(EXTRACT(MONTH FROM started_at AT TIME ZONE 'UTC')::INT::TEXT, 2, '0')
            ) STORED
        )
        """,
    )
    # Tenant-scoped daily lookups (dashboards, MV refresh).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sales_agent_llm_call_tenant_day
        ON sales_agent_llm_call (tenant_id, occurred_on)
        """,
    )
    # Per-lead reconstruction (sales_audit dual-read window).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sales_agent_llm_call_lead
        ON sales_agent_llm_call (tenant_id, lead_id, started_at DESC)
        """,
    )
    # Per-turn (admin trace timeline + per-turn cost).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sales_agent_llm_call_turn
        ON sales_agent_llm_call (turn_id)
        """,
    )
    # Slice by model under a tenant (per-model cost / hit-rate).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sales_agent_llm_call_tenant_model_day
        ON sales_agent_llm_call (tenant_id, model_responded, occurred_on)
        """,
    )
    # Quick error scan for alerting (partial = small + cheap).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sales_agent_llm_call_errors
        ON sales_agent_llm_call (tenant_id, started_at DESC)
        WHERE status = 'error'
        """,
    )

    # ── sales_agent_trace_event ──────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sales_agent_trace_event (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            lead_id UUID NOT NULL,
            channel_type VARCHAR(32) NOT NULL,
            turn_id UUID NOT NULL,
            span_id UUID NOT NULL,
            parent_span_id UUID,
            event_type VARCHAR(32) NOT NULL,
            name VARCHAR(128),
            data JSONB NOT NULL DEFAULT '{}'::jsonb,
            duration_ms INTEGER,
            status VARCHAR(16) NOT NULL DEFAULT 'ok',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sales_agent_trace_event_lead
        ON sales_agent_trace_event (tenant_id, lead_id, created_at DESC)
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sales_agent_trace_event_turn
        ON sales_agent_trace_event (turn_id, created_at)
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sales_agent_trace_event_tenant_time
        ON sales_agent_trace_event (tenant_id, created_at DESC)
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sales_agent_trace_event_errors
        ON sales_agent_trace_event (tenant_id, created_at DESC)
        WHERE status = 'error'
        """,
    )

    # ── sales_agent_routing_log ──────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS sales_agent_routing_log (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            lead_id UUID NOT NULL,
            channel_type VARCHAR(32) NOT NULL,
            turn_id UUID NOT NULL,
            stage VARCHAR(32) NOT NULL,
            lead_score INTEGER,
            tier_selected TEXT NOT NULL,
            specialist_routed TEXT NOT NULL,
            reason TEXT NOT NULL,
            confidence NUMERIC(4,3),
            user_msg_length INTEGER NOT NULL,
            tools_available INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sales_agent_routing_log_tenant_time
        ON sales_agent_routing_log (tenant_id, created_at DESC)
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sales_agent_routing_log_lead
        ON sales_agent_routing_log (tenant_id, lead_id, created_at DESC)
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_sales_agent_routing_log_turn
        ON sales_agent_routing_log (turn_id)
        """,
    )


def downgrade() -> None:
    """Drop the three sales-agent observability tables. Idempotent."""
    op.execute("DROP TABLE IF EXISTS sales_agent_routing_log CASCADE")
    op.execute("DROP TABLE IF EXISTS sales_agent_trace_event CASCADE")
    op.execute("DROP TABLE IF EXISTS sales_agent_llm_call CASCADE")
