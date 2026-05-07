"""Eval simulator observability tables (Story B eval-foundation-simulator-homologation).

Idempotente raw SQL IF NOT EXISTS (regla backend-migrations.md).

Creates 3 new tables + 6 indexes for the eval_simulator cost bucket:
  - eval_simulator_llm_call  : LLM call audit rows (cost bucket separation H6)
  - eval_simulator_trace_event : trace events per simulation turn
  - eval_synthetic_tenants   : lookup table for synthetic tenant isolation (D2/D4)

Pattern parity: campaigns/observability (Alembic 083). See 03-arch-be.md §1.

Decision D-BE-1: agent_kind NOT a Postgres enum — registry discriminator (str).
Decision D-BE-2: table mirror campaigns schema verbatim minus lead_id NOT NULL→NULL
                 + retention 30d default (synthetic, no audit obligation).
Decision D-BE-4: is_eval_synthetic marker via lookup table, NOT column in business tables.

Revision ID: 125_add_eval_simulator_observability_tables
Revises: 124_drop_tenant_provider_api_keys
Create Date: 2026-05-07
"""

from alembic import op

revision = "125_add_eval_simulator_observability_tables"
down_revision = "124_drop_tenant_provider_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create eval_simulator_llm_call, eval_simulator_trace_event, eval_synthetic_tenants tables."""
    # ── eval_simulator_llm_call ────────────────────────────────────────────
    # Mirror semantico de campaign_llm_call (083) + sales_agent_llm_call.
    # Differences vs campaigns:
    #   - lead_id: NULL (eval simulator does not use per-lead audit)
    #   - eval_metadata: JSONB NOT NULL (mandatory H5 tags: eval_run_kind, archetype_slug,
    #     actor_profile_id, trial_n, simulation_id, run_id)
    #   - cost_usd: NULL allowed (paridad 086_llm_call_cost_usd_nullable)
    #   - channel_type DEFAULT 'eval_simulator'
    op.execute("""
        CREATE TABLE IF NOT EXISTS eval_simulator_llm_call (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            lead_id UUID NULL,
            channel_type VARCHAR(32) NOT NULL DEFAULT 'eval_simulator',
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
            cost_usd NUMERIC(16,10) NULL,
            tenant_currency CHAR(3),
            fx_rate_to_tenant NUMERIC(16,8),
            fx_rate_source VARCHAR(32),
            cost_tenant_currency NUMERIC(16,8),
            started_at TIMESTAMPTZ NOT NULL,
            duration_ms INTEGER NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'ok',
            error_type VARCHAR(64),
            eval_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            occurred_on DATE GENERATED ALWAYS AS ((started_at AT TIME ZONE 'UTC')::date) STORED,
            occurred_year_month VARCHAR(7) GENERATED ALWAYS AS (
                EXTRACT(YEAR FROM started_at AT TIME ZONE 'UTC')::INT::TEXT
                || '-'
                || LPAD(EXTRACT(MONTH FROM started_at AT TIME ZONE 'UTC')::INT::TEXT, 2, '0')
            ) STORED
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_simulator_llm_call_tenant_day
        ON eval_simulator_llm_call (tenant_id, occurred_on)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_simulator_llm_call_turn
        ON eval_simulator_llm_call (turn_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_simulator_llm_call_sim_id
        ON eval_simulator_llm_call ((eval_metadata->>'simulation_id'))
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_simulator_llm_call_run_id
        ON eval_simulator_llm_call ((eval_metadata->>'run_id'))
    """)

    # ── eval_simulator_trace_event ─────────────────────────────────────────
    # Mirror semantico de campaign_trace_event (083) + eval_metadata JSONB (H5).
    op.execute("""
        CREATE TABLE IF NOT EXISTS eval_simulator_trace_event (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            lead_id UUID NULL,
            channel_type VARCHAR(32) NOT NULL DEFAULT 'eval_simulator',
            turn_id UUID NOT NULL,
            span_id UUID NOT NULL,
            parent_span_id UUID,
            event_type VARCHAR(32) NOT NULL,
            name VARCHAR(128),
            data JSONB NOT NULL DEFAULT '{}'::jsonb,
            duration_ms INTEGER,
            status VARCHAR(16) NOT NULL DEFAULT 'ok',
            eval_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_simulator_trace_event_tenant_turn
        ON eval_simulator_trace_event (tenant_id, turn_id, created_at)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_simulator_trace_event_sim_id
        ON eval_simulator_trace_event ((eval_metadata->>'simulation_id'))
    """)

    # ── eval_synthetic_tenants ─────────────────────────────────────────────
    # Lookup table for synthetic tenant isolation (D4 arch decision).
    # tenant_id = uuid5(NAMESPACE_DNS, f"eval-{slug}") per D2.
    # Prod Streamlit queries can filter by excluding rows in this table.
    op.execute("""
        CREATE TABLE IF NOT EXISTS eval_synthetic_tenants (
            tenant_id UUID PRIMARY KEY,
            archetype_slug VARCHAR(64) NOT NULL,
            seeded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at TIMESTAMPTZ NULL
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_eval_synthetic_tenants_slug
        ON eval_synthetic_tenants (archetype_slug)
        WHERE deleted_at IS NULL
    """)


def downgrade() -> None:
    """Drop eval simulator tables (safe — eval-only, no production data)."""
    op.execute("DROP TABLE IF EXISTS eval_simulator_trace_event CASCADE")
    op.execute("DROP TABLE IF EXISTS eval_simulator_llm_call CASCADE")
    op.execute("DROP TABLE IF EXISTS eval_synthetic_tenants CASCADE")
