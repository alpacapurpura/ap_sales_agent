"""S9 — sales_agent payment lifecycle tables.

Adds:

1. ``payment_link`` — one row per payment link created by the agent.
   Status transitions: pending → paid / failed / cancelled / expired / refunded.

2. ``payment_grant_audit`` — append-only log of every access-delivery attempt.
   UNIQUE (tenant_id, lead_id, offer_id, payment_id) prevents duplicate grants.
   No updated_at column (append-only invariant).

3. ``payment_webhook_event`` — idempotency dedup table for incoming webhooks.
   UNIQUE (provider, external_id, event_type, occurred_at).

4. ``agent_state_checkpoints.payment_state`` — JSONB column tracking active
   payment links per conversation (mirrors ``scheduled_meetings`` from S8).

Revision: 081_sales_agent_payment_lifecycle
"""

from __future__ import annotations

from alembic import op

revision: str = "081_sales_agent_payment_lifecycle"
down_revision: str | None = "080_sales_agent_scheduler_meetings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create payment tables + JSONB column."""
    # 1. payment_link
    op.execute("""
        CREATE TABLE IF NOT EXISTS payment_link (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID        NOT NULL,
            lead_id         UUID        NOT NULL,
            offer_id        UUID        NOT NULL,
            provider        TEXT        NOT NULL,
            external_id     TEXT        NOT NULL,
            url             TEXT        NOT NULL,
            amount          NUMERIC(12,2) NOT NULL,
            currency        CHAR(3)     NOT NULL,
            status          TEXT        NOT NULL DEFAULT 'pending',
            metadata        JSONB       NOT NULL DEFAULT '{}',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            expires_at      TIMESTAMPTZ,
            CONSTRAINT uq_payment_link_provider_external
                UNIQUE (tenant_id, provider, external_id)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_payment_link_tenant_lead
            ON payment_link (tenant_id, lead_id)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_payment_link_status
            ON payment_link (tenant_id, status)
            WHERE status = 'pending'
    """)

    # 2. payment_grant_audit (append-only — no updated_at)
    op.execute("""
        CREATE TABLE IF NOT EXISTS payment_grant_audit (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID        NOT NULL,
            lead_id         UUID        NOT NULL,
            offer_id        UUID        NOT NULL,
            payment_id      UUID        NOT NULL,
            channels        JSONB       NOT NULL DEFAULT '[]',
            status          TEXT        NOT NULL DEFAULT 'granted',
            failure_detail  JSONB       NOT NULL DEFAULT '{}',
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_payment_grant_natural_key
                UNIQUE (tenant_id, lead_id, offer_id, payment_id)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_payment_grant_audit_tenant
            ON payment_grant_audit (tenant_id, created_at)
    """)

    # 3. payment_webhook_event (idempotency dedup)
    op.execute("""
        CREATE TABLE IF NOT EXISTS payment_webhook_event (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID,
            provider        TEXT        NOT NULL,
            external_id     TEXT        NOT NULL,
            event_type      TEXT        NOT NULL,
            occurred_at     TIMESTAMPTZ NOT NULL,
            payload         JSONB       NOT NULL DEFAULT '{}',
            received_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_payment_webhook_dedup
                UNIQUE (provider, external_id, event_type, occurred_at)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_payment_webhook_tenant_received
            ON payment_webhook_event (tenant_id, received_at)
    """)

    # 4. payment_state JSONB column on agent_state_checkpoints
    op.execute("""
        ALTER TABLE agent_state_checkpoints
            ADD COLUMN IF NOT EXISTS payment_state JSONB NOT NULL DEFAULT '[]'
    """)


def downgrade() -> None:
    """Drop payment tables + column."""
    op.execute("""
        ALTER TABLE agent_state_checkpoints
            DROP COLUMN IF EXISTS payment_state
    """)
    op.execute("DROP TABLE IF EXISTS payment_webhook_event")
    op.execute("DROP TABLE IF EXISTS payment_grant_audit")
    op.execute("DROP TABLE IF EXISTS payment_link")
