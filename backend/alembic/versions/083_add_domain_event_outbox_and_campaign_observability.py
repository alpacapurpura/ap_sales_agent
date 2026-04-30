"""Outbox table + campaign observability tables (PI-1 S0 PR-1).

Idempotente raw SQL IF NOT EXISTS (regla backend-migrations.md).

Revision ID: 083_add_domain_event_outbox_and_campaign_observability
Revises: 082_sales_agent_workflow_metric
Create Date: 2026-04-29
"""

from alembic import op

revision = "083_add_domain_event_outbox_and_campaign_observability"
down_revision = "082_sales_agent_workflow_metric"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create domain_event_outbox, campaign_llm_call, campaign_trace_event tables."""
    # ── domain_event_outbox ─────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS domain_event_outbox (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            event_name VARCHAR(128) NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            idempotency_key VARCHAR(256) NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'pending',
            retry_count INTEGER NOT NULL DEFAULT 0,
            last_error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            dispatched_at TIMESTAMPTZ
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_outbox_tenant_idem
        ON domain_event_outbox (tenant_id, idempotency_key)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_outbox_pending
        ON domain_event_outbox (status, created_at)
        WHERE status = 'pending'
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_outbox_tenant_created
        ON domain_event_outbox (tenant_id, created_at DESC)
    """)

    # ── campaign_llm_call ───────────────────────────────────────────────
    # Mirror semantico de sales_agent_llm_call (078_*.py) + has_lead_id=True.
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign_llm_call (
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
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_llm_call_tenant_day
        ON campaign_llm_call (tenant_id, occurred_on)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_llm_call_lead
        ON campaign_llm_call (tenant_id, lead_id, started_at DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_llm_call_turn
        ON campaign_llm_call (turn_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_llm_call_tenant_model_day
        ON campaign_llm_call (tenant_id, model_responded, occurred_on)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_llm_call_errors
        ON campaign_llm_call (tenant_id, started_at DESC)
        WHERE status = 'error'
    """)

    # ── campaign_trace_event ────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign_trace_event (
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
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_trace_event_lead
        ON campaign_trace_event (tenant_id, lead_id, created_at DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_trace_event_turn
        ON campaign_trace_event (turn_id, created_at)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_trace_event_tenant_time
        ON campaign_trace_event (tenant_id, created_at DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_trace_event_errors
        ON campaign_trace_event (tenant_id, created_at DESC)
        WHERE status = 'error'
    """)


def downgrade() -> None:
    """Explicit NO-OP — outbox + observability data is operational, never dropped."""
