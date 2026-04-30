"""campaigns audit log — campaign_audit table + indices.

PI-1 S2 PR-5 orchestrator-and-workers.

Idempotent raw SQL (IF NOT EXISTS) per backend-migrations.md.
NO ALTER existing tables. ZERO conflict potential.

Revision ID: 113_campaigns_audit_log
Revises: 112_campaigns_domain
Create Date: 2026-04-30
"""

from alembic import op

revision = "113_campaigns_audit_log"
down_revision = "112_campaigns_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create campaign_audit table and indices idempotently."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS campaign_audit (
            id                  UUID            PRIMARY KEY,
            tenant_id           UUID            NOT NULL,
            campaign_id         UUID            NULL,
            campaign_task_id    UUID            NULL,
            event_type          VARCHAR(50)     NOT NULL,
            actor               VARCHAR(50)     NOT NULL,
            payload             JSONB           NOT NULL DEFAULT '{}'::jsonb,
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_campaign_audit_actor_nonempty CHECK (length(actor) > 0),
            CONSTRAINT ck_campaign_audit_event_type_nonempty CHECK (length(event_type) > 0)
        )
    """)
    # Hot path: "todos los eventos de esta campaña ordenados desc"
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_audit_tenant_campaign_created
            ON campaign_audit (tenant_id, campaign_id, created_at DESC)
            WHERE campaign_id IS NOT NULL
    """)
    # Hot path: retention purge (worker scans by created_at globally)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_audit_created
            ON campaign_audit (created_at)
    """)
    # Debug: eventos por task específica
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_campaign_audit_task
            ON campaign_audit (campaign_task_id)
            WHERE campaign_task_id IS NOT NULL
    """)


def downgrade() -> None:
    """Drop campaign_audit indices and table."""
    op.execute("DROP INDEX IF EXISTS ix_campaign_audit_task")
    op.execute("DROP INDEX IF EXISTS ix_campaign_audit_created")
    op.execute("DROP INDEX IF EXISTS ix_campaign_audit_tenant_campaign_created")
    op.execute("DROP TABLE IF EXISTS campaign_audit")
