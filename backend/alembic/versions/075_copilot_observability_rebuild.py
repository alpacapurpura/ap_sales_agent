"""Phase 1 of the copilot observability rebuild — three new tables.

Adds the foundation required to switch the copilot to a single, cohesive
observability subscriber in Phase 2. None of these tables are read or
written from the hot path until the atomic switch lands.

* ``copilot_llm_call``         — one immutable row per LLM invocation,
  carrying token counts, cached tokens, snapshot pricing, status. Backs
  every billing query and the per-tenant cost dashboard.
* ``model_pricing_snapshot``    — point-in-time pricing per (provider,
  model). The active row has ``valid_to IS NULL``; the LiteLLM sync
  worker (``observability/workers/pricing_sync_task.py``) closes outdated
  rows and inserts new ones daily so historical cost reconstruction stays
  consistent.
* ``tenant_billing_config``     — per-tenant cycle anchor day, billing
  currency, FX source. Drives the 25-25 cycle and currency conversion in
  reports.

Idempotent — every statement uses ``IF NOT EXISTS`` (regla
``.claude/rules/backend-migrations.md``). Re-running ``alembic upgrade
head`` is a no-op.

Schema source of truth: ``docs/domains/copilot/observability-rebuild-2026-04
/ARCHITECTURE.md`` §4.2.

Revision ID: 075_copilot_observability_rebuild
Revises: 074_mutation_journal_natural_key_idempotent
Create Date: 2026-04-26 22:00:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "075_copilot_observability_rebuild"
down_revision: str | None = "074_mutation_journal_natural_key_idempotent"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create observability tables + indexes. Idempotent."""
    # ── copilot_llm_call ────────────────────────────────────────────────
    # Event-sourced LLM call log. Pricing values are denormalised at write
    # time (snapshot via pricing_version_id) so cost cannot drift if the
    # upstream LiteLLM JSON changes after the fact.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS copilot_llm_call (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            user_id UUID,
            conversation_id UUID,
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
        CREATE INDEX IF NOT EXISTS ix_llm_call_tenant_day
        ON copilot_llm_call (tenant_id, occurred_on)
        """,
    )
    # Per-turn reconstruction (admin trace timeline + per-turn cost).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_llm_call_turn
        ON copilot_llm_call (turn_id)
        """,
    )
    # Slice by model under a tenant (per-model cost / hit-rate).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_llm_call_tenant_model_day
        ON copilot_llm_call (tenant_id, model_responded, occurred_on)
        """,
    )
    # Quick error scan for alerting (partial = small + cheap).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_llm_call_errors
        ON copilot_llm_call (tenant_id, started_at DESC)
        WHERE status = 'error'
        """,
    )

    # ── model_pricing_snapshot ──────────────────────────────────────────
    # Point-in-time pricing. The active row has valid_to=NULL; closed rows
    # carry the timestamp at which the LiteLLM diff detected a change.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS model_pricing_snapshot (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            provider VARCHAR(32) NOT NULL,
            model VARCHAR(128) NOT NULL,
            input_cost_per_token NUMERIC(14,12) NOT NULL,
            output_cost_per_token NUMERIC(14,12) NOT NULL,
            cache_read_cost_per_token NUMERIC(14,12) DEFAULT 0,
            cache_write_cost_per_token NUMERIC(14,12) DEFAULT 0,
            batch_input_cost_per_token NUMERIC(14,12),
            source VARCHAR(32) NOT NULL,
            source_etag VARCHAR(64),
            valid_from TIMESTAMPTZ NOT NULL,
            valid_to TIMESTAMPTZ,
            raw_payload JSONB NOT NULL
        )
        """,
    )
    # Single-active-row guarantee per (provider, model). Resolver hits this
    # in the steady-state cache-miss path.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_pricing_active
        ON model_pricing_snapshot (provider, model)
        WHERE valid_to IS NULL
        """,
    )
    # Historical lookup (cost reconstruction at ts).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_pricing_lookup
        ON model_pricing_snapshot (provider, model, valid_from DESC)
        """,
    )

    # ── tenant_billing_config ───────────────────────────────────────────
    # Anchor day defaults to 25 (Nicolify cycle: 25 → 25). Billing currency
    # defaults to USD; FX source defaults to frankfurter.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenant_billing_config (
            tenant_id UUID PRIMARY KEY,
            billing_cycle_anchor_day SMALLINT NOT NULL DEFAULT 25,
            billing_currency CHAR(3) NOT NULL DEFAULT 'USD',
            fx_source VARCHAR(32) NOT NULL DEFAULT 'frankfurter',
            flat_fee_amount NUMERIC(14,2),
            cost_alert_threshold_usd NUMERIC(14,2),
            notes TEXT,
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
    )


def downgrade() -> None:
    """Drop the three observability tables. Idempotent."""
    op.execute("DROP TABLE IF EXISTS tenant_billing_config CASCADE")
    op.execute("DROP TABLE IF EXISTS model_pricing_snapshot CASCADE")
    op.execute("DROP TABLE IF EXISTS copilot_llm_call CASCADE")
