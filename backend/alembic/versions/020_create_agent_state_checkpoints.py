"""create agent_state_checkpoints table

Revision ID: 020_create_agent_state_checkpoints
Revises: 019_add_message_id_idx
Create Date: 2026-03-30
"""
from typing import Sequence, Union

from alembic import op

revision = "020_create_agent_state_checkpoints"
down_revision = "019_add_message_id_idx"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS agent_state_checkpoints (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id VARCHAR(255) NOT NULL,
            tenant_id UUID NOT NULL,
            lead_id UUID NOT NULL,
            customer_profile_id UUID,
            channel_type VARCHAR(50),
            current_stage VARCHAR(50) NOT NULL DEFAULT 'rapport',
            lead_score INTEGER NOT NULL DEFAULT 0,
            lead_data JSONB NOT NULL DEFAULT '{}'::jsonb,
            buying_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
            objection_history JSONB NOT NULL DEFAULT '[]'::jsonb,
            qualification_answers JSONB NOT NULL DEFAULT '{}'::jsonb,
            turn_count INTEGER NOT NULL DEFAULT 0,
            last_specialist VARCHAR(50),
            close_strategy VARCHAR(50),
            metadata_info JSONB,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            deleted_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_checkpoint_session ON agent_state_checkpoints (session_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_checkpoint_tenant ON agent_state_checkpoints (tenant_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_checkpoint_lead ON agent_state_checkpoints (lead_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_checkpoint_tenant_lead_active ON agent_state_checkpoints (tenant_id, lead_id, is_active);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS agent_state_checkpoints;")
