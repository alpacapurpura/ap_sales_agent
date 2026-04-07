"""Add question fatigue tracking fields to agent_state_checkpoints.

New columns for tracking consecutive qualifier questions (fatigue detection)
and follow-up cadence scheduling.

Revision ID: 037_add_question_fatigue_fields
Revises: 036_add_deleted_at_channel_connections
"""

from alembic import op

revision = "037_add_question_fatigue_fields"
down_revision = "036_add_deleted_at_channel_connections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE agent_state_checkpoints "
        "ADD COLUMN IF NOT EXISTS consecutive_questions INTEGER NOT NULL DEFAULT 0"
    )
    op.execute(
        "ALTER TABLE agent_state_checkpoints "
        "ADD COLUMN IF NOT EXISTS follow_up_cadence JSONB NULL"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE agent_state_checkpoints DROP COLUMN IF EXISTS consecutive_questions"
    )
    op.execute(
        "ALTER TABLE agent_state_checkpoints DROP COLUMN IF EXISTS follow_up_cadence"
    )
