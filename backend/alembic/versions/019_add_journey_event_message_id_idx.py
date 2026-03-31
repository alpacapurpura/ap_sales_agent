"""Add partial index on journey_events for message_id dedup

Revision ID: 019_add_message_id_idx
Revises: 018_add_archetype_columns
Create Date: 2026-03-30
"""
from typing import Sequence, Union
from alembic import op

# revision identifiers
revision = "019_add_message_id_idx"
down_revision = "018_add_archetype_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Partial index on journey_events (properties->>'message_id').

    Used for dedup when syncing IG DM conversations (Conversations API)
    against webhook-created events. Only indexes rows that have a message_id.
    """
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_journey_events_message_id
        ON journey_events ((properties->>'message_id'))
        WHERE properties->>'message_id' IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_journey_events_message_id")
