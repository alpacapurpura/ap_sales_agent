"""billing_compliance_tables.

plan_config, tenant_subscription, channel_blacklist, lead_opt_ins, mv_refresh_log, leads.country.

PI-1 S0 PR-2 billing-and-compliance.

Idempotent raw SQL (IF NOT EXISTS) per backend-migrations.md rules.
Partial unique index for is_default invariant (PM Q6).
Seeds 5 plan rows with ON CONFLICT DO NOTHING.
Backfills lead_opt_ins from messages.role='user' (last 30 days).
plan_config + mv_refresh_log are global (no tenant_id) — allowlist exception documented.

Revision ID: 110_billing_compliance_tables
Revises: 085_copilot_tenant_limits
Create Date: 2026-04-29
"""

from alembic import op

revision = "110_billing_compliance_tables"
down_revision = "085_copilot_tenant_limits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. plan_config — global catalog (no tenant_id)
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS plan_config (
            plan_id             VARCHAR(32)     PRIMARY KEY,
            display_name        VARCHAR(64)     NOT NULL,
            llm_budget_total_usd NUMERIC(10,2)  NOT NULL,
            sales_agent_reserved_pct NUMERIC(4,3) NOT NULL DEFAULT 0.500,
            max_outbound_msg_per_day INTEGER      NULL,
            max_campaigns_active    INTEGER       NULL,
            max_segment_size        INTEGER       NULL,
            max_contacts_total      INTEGER       NULL,
            features            JSONB            NOT NULL DEFAULT '{}',
            is_active           BOOLEAN          NOT NULL DEFAULT TRUE,
            is_default          BOOLEAN          NOT NULL DEFAULT FALSE,
            created_at          TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_plan_config_budget_positive
                CHECK (llm_budget_total_usd > 0),
            CONSTRAINT ck_plan_config_sa_pct_range
                CHECK (sales_agent_reserved_pct >= 0 AND sales_agent_reserved_pct <= 1),
            CONSTRAINT ck_plan_config_outbound_nonneg
                CHECK (max_outbound_msg_per_day IS NULL OR max_outbound_msg_per_day >= 0)
        )
    """)

    # Partial unique index: exactly one default plan at a time (PM Q6)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_plan_config_one_default
            ON plan_config (is_default)
            WHERE is_default = TRUE
    """)

    # ------------------------------------------------------------------
    # 2. Seed 5 plan rows — ON CONFLICT DO NOTHING (idempotent)
    # ------------------------------------------------------------------
    op.execute("""
        INSERT INTO plan_config
            (plan_id, display_name, llm_budget_total_usd, sales_agent_reserved_pct,
             max_outbound_msg_per_day, is_default)
        VALUES
            ('free',         'Gratuito',     5.00,  0.500, 100,   TRUE),
            ('basic',        'Básico',       15.00, 0.500, 500,   FALSE),
            ('intermediate', 'Intermedio',   30.00, 0.500, 2000,  FALSE),
            ('advanced',     'Avanzado',     45.00, 0.500, 5000,  FALSE),
            ('ultra',        'Ultra',        95.00, 0.500, 20000, FALSE)
        ON CONFLICT (plan_id) DO NOTHING
    """)

    # ------------------------------------------------------------------
    # 3. tenant_subscription — 1:1 tenant ↔ plan
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenant_subscription (
            tenant_id           UUID            PRIMARY KEY,
            plan_id             VARCHAR(32)     NOT NULL REFERENCES plan_config(plan_id),
            cycle_anchor_day    INTEGER         NOT NULL DEFAULT 1,
            custom_overrides    JSONB           NOT NULL DEFAULT '{}',
            trial_ends_at       TIMESTAMPTZ     NULL,
            activated_at        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            deleted_at          TIMESTAMPTZ     NULL,
            CONSTRAINT ck_tenant_subscription_anchor_range
                CHECK (cycle_anchor_day BETWEEN 1 AND 28)
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_tenant_subscription_plan_id
            ON tenant_subscription (plan_id)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_tenant_subscription_active
            ON tenant_subscription (tenant_id)
            WHERE deleted_at IS NULL
    """)

    # ------------------------------------------------------------------
    # 4. channel_blacklist — compliance per-tenant per-channel
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS channel_blacklist (
            id                  UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           UUID            NOT NULL,
            channel             VARCHAR(32)     NOT NULL,
            identifier          VARCHAR(255)    NOT NULL,
            reason              VARCHAR(255)    NULL,
            created_by_user_id  UUID            NULL,
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            deleted_at          TIMESTAMPTZ     NULL
        )
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_channel_blacklist_tenant_channel_identifier
            ON channel_blacklist (tenant_id, channel, identifier)
            WHERE deleted_at IS NULL
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_channel_blacklist_lookup
            ON channel_blacklist (tenant_id, channel, identifier)
            WHERE deleted_at IS NULL
    """)

    # ------------------------------------------------------------------
    # 5. lead_opt_ins — PM Q2 production-grade opt-in audit trail
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS lead_opt_ins (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID        NOT NULL,
            lead_id         UUID        NOT NULL REFERENCES leads(id),
            channel         VARCHAR(32) NOT NULL,
            opted_in_at     TIMESTAMPTZ NULL,
            opted_out_at    TIMESTAMPTZ NULL,
            source          VARCHAR(24) NOT NULL
                                CHECK (source IN ('webhook','manual','imported','inferred_message')),
            evidence        JSONB       NOT NULL DEFAULT '{}',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_lead_opt_ins_tenant_lead_channel
            ON lead_opt_ins (tenant_id, lead_id, channel)
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_lead_opt_ins_lookup
            ON lead_opt_ins (tenant_id, lead_id, channel, opted_in_at, opted_out_at)
    """)

    # ------------------------------------------------------------------
    # 6. mv_refresh_log — PM Q4 exact MV freshness signal (global, no tenant_id)
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS mv_refresh_log (
            id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            mv_name             VARCHAR(64) NOT NULL,
            refreshed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            refresh_duration_ms INTEGER     NULL,
            rows_affected       INTEGER     NULL,
            status              VARCHAR(16) NOT NULL DEFAULT 'ok'
                                    CHECK (status IN ('ok', 'error', 'skipped'))
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_mv_refresh_log_mv_name_recent
            ON mv_refresh_log (mv_name, refreshed_at)
    """)

    # ------------------------------------------------------------------
    # 7. leads.country — PM Q3 country-block primary signal (ISO 3166-1 alpha-2)
    # ------------------------------------------------------------------
    op.execute("""
        ALTER TABLE leads ADD COLUMN IF NOT EXISTS country VARCHAR(2) NULL
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_leads_country
            ON leads (tenant_id, country)
            WHERE country IS NOT NULL
    """)

    # ------------------------------------------------------------------
    # 8. Backfill lead_opt_ins from inferred messages (last 30 days)
    #    lead_id = messages.user_id WHERE role = 'user'
    #    channel = messages.channel (skip if NULL)
    # ------------------------------------------------------------------
    op.execute("""
        INSERT INTO lead_opt_ins (id, tenant_id, lead_id, channel, opted_in_at, source)
        SELECT
            gen_random_uuid(),
            m.tenant_id,
            m.user_id,
            m.channel,
            MIN(m.created_at),
            'inferred_message'
        FROM messages m
        WHERE m.role = 'user'
          AND m.user_id IS NOT NULL
          AND m.channel IS NOT NULL
          AND m.tenant_id IS NOT NULL
          AND m.created_at > NOW() - INTERVAL '30 days'
        GROUP BY m.tenant_id, m.user_id, m.channel
        ON CONFLICT (tenant_id, lead_id, channel) DO NOTHING
    """)


def downgrade() -> None:
    # Reverse order
    op.execute("DROP INDEX IF EXISTS ix_leads_country")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS country")

    op.execute("DROP INDEX IF EXISTS ix_mv_refresh_log_mv_name_recent")
    op.execute("DROP TABLE IF EXISTS mv_refresh_log")

    op.execute("DROP INDEX IF EXISTS ix_lead_opt_ins_lookup")
    op.execute("DROP INDEX IF EXISTS uq_lead_opt_ins_tenant_lead_channel")
    op.execute("DROP TABLE IF EXISTS lead_opt_ins")

    op.execute("DROP INDEX IF EXISTS ix_channel_blacklist_lookup")
    op.execute("DROP INDEX IF EXISTS uq_channel_blacklist_tenant_channel_identifier")
    op.execute("DROP TABLE IF EXISTS channel_blacklist")

    op.execute("DROP INDEX IF EXISTS ix_tenant_subscription_active")
    op.execute("DROP INDEX IF EXISTS ix_tenant_subscription_plan_id")
    op.execute("DROP TABLE IF EXISTS tenant_subscription")

    op.execute("DROP INDEX IF EXISTS uq_plan_config_one_default")
    op.execute("DROP TABLE IF EXISTS plan_config")
