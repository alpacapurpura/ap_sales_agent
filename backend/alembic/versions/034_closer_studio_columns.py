"""closer_studio_columns

Adds handler control, frozen detection, and unread tracking columns
to agent_state_checkpoints for Closer Studio. Adds sender_source to messages.

Revision ID: 034_closer_studio_columns
Revises: 033_add_period_aware_columns
Create Date: 2026-04-03
"""

from alembic import op

revision = "034_closer_studio_columns"
down_revision = "033_add_period_aware_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── agent_state_checkpoints: Closer Studio handler control ──
    op.execute("""
        ALTER TABLE agent_state_checkpoints
        ADD COLUMN IF NOT EXISTS handler_mode VARCHAR(20) NOT NULL DEFAULT 'ai'
    """)
    op.execute("""
        ALTER TABLE agent_state_checkpoints
        ADD COLUMN IF NOT EXISTS paused_at TIMESTAMP NULL
    """)
    op.execute("""
        ALTER TABLE agent_state_checkpoints
        ADD COLUMN IF NOT EXISTS paused_by UUID NULL
    """)
    op.execute("""
        ALTER TABLE agent_state_checkpoints
        ADD COLUMN IF NOT EXISTS resume_objective TEXT NULL
    """)

    # ── agent_state_checkpoints: frozen detection ──
    op.execute("""
        ALTER TABLE agent_state_checkpoints
        ADD COLUMN IF NOT EXISTS frozen_reason VARCHAR(100) NULL
    """)
    op.execute("""
        ALTER TABLE agent_state_checkpoints
        ADD COLUMN IF NOT EXISTS frozen_at TIMESTAMP NULL
    """)
    op.execute("""
        ALTER TABLE agent_state_checkpoints
        ADD COLUMN IF NOT EXISTS frozen_diagnosis JSONB NULL
    """)

    # ── agent_state_checkpoints: unread tracking ──
    op.execute("""
        ALTER TABLE agent_state_checkpoints
        ADD COLUMN IF NOT EXISTS last_human_message_at TIMESTAMP NULL
    """)
    op.execute("""
        ALTER TABLE agent_state_checkpoints
        ADD COLUMN IF NOT EXISTS unread_count INTEGER NOT NULL DEFAULT 0
    """)

    # ── Indices ──
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_checkpoint_handler_mode
        ON agent_state_checkpoints (tenant_id, handler_mode, is_active)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_checkpoint_frozen
        ON agent_state_checkpoints (tenant_id, frozen_at, is_active)
    """)

    # ── messages: sender_source (table may not exist on fresh DB) ──
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'messages'
            ) THEN
                ALTER TABLE messages
                ADD COLUMN IF NOT EXISTS sender_source VARCHAR(20) NOT NULL
                    DEFAULT 'auto';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'messages'
            ) THEN
                ALTER TABLE messages DROP COLUMN IF EXISTS sender_source;
            END IF;
        END $$;
    """)
    op.execute("DROP INDEX IF EXISTS ix_checkpoint_frozen")
    op.execute("DROP INDEX IF EXISTS ix_checkpoint_handler_mode")
    op.execute("ALTER TABLE agent_state_checkpoints DROP COLUMN IF EXISTS unread_count")
    op.execute(
        "ALTER TABLE agent_state_checkpoints DROP COLUMN IF EXISTS last_human_message_at"
    )
    op.execute(
        "ALTER TABLE agent_state_checkpoints DROP COLUMN IF EXISTS frozen_diagnosis"
    )
    op.execute("ALTER TABLE agent_state_checkpoints DROP COLUMN IF EXISTS frozen_at")
    op.execute(
        "ALTER TABLE agent_state_checkpoints DROP COLUMN IF EXISTS frozen_reason"
    )
    op.execute(
        "ALTER TABLE agent_state_checkpoints DROP COLUMN IF EXISTS resume_objective"
    )
    op.execute("ALTER TABLE agent_state_checkpoints DROP COLUMN IF EXISTS paused_by")
    op.execute("ALTER TABLE agent_state_checkpoints DROP COLUMN IF EXISTS paused_at")
    op.execute("ALTER TABLE agent_state_checkpoints DROP COLUMN IF EXISTS handler_mode")
