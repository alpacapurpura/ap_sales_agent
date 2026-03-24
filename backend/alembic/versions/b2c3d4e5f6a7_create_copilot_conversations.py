"""create copilot_conversations table

Revision ID: b2c3d4e5f6a7
Revises: e3f4a5b6c7d8
Create Date: 2026-03-24

"""
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "e3f4a5b6c7d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS copilot_conversations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            user_id UUID NOT NULL,
            title VARCHAR(255),
            messages JSONB NOT NULL DEFAULT '[]'::jsonb,
            client_context JSONB,
            summary TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_conversations_tenant_id
        ON copilot_conversations (tenant_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_conversations_user_id
        ON copilot_conversations (user_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_conversations_tenant_user_updated
        ON copilot_conversations (tenant_id, user_id, updated_at DESC);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS copilot_conversations;")
