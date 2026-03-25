"""create copilot_events table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-03-25

"""
from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS copilot_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            user_id UUID NOT NULL,
            conversation_id UUID,
            event_type VARCHAR(50) NOT NULL,
            event_data JSONB DEFAULT '{}'::jsonb,
            route VARCHAR(255),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_copilot_events_tenant_created
        ON copilot_events (tenant_id, created_at DESC) WHERE deleted_at IS NULL;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_copilot_events_tenant_type
        ON copilot_events (tenant_id, event_type) WHERE deleted_at IS NULL;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_copilot_events_tenant_user_created
        ON copilot_events (tenant_id, user_id, created_at DESC) WHERE deleted_at IS NULL;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS copilot_events;")
