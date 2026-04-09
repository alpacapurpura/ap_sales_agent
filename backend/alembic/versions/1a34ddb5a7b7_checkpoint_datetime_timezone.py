"""checkpoint_datetime_timezone

Revision ID: 1a34ddb5a7b7
Revises: 037_add_question_fatigue_fields
Create Date: 2026-04-09 06:55:53.648977

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1a34ddb5a7b7"
down_revision: str | None = "037_add_question_fatigue_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for col in [
        "paused_at",
        "frozen_at",
        "last_human_message_at",
        "deleted_at",
        "created_at",
        "updated_at",
    ]:
        op.execute(
            f"ALTER TABLE agent_state_checkpoints "
            f"ALTER COLUMN {col} TYPE TIMESTAMPTZ USING {col} AT TIME ZONE 'UTC'"
        )
    op.execute(
        "ALTER TABLE agent_state_checkpoints ALTER COLUMN created_at SET DEFAULT now()"
    )
    op.execute(
        "ALTER TABLE agent_state_checkpoints ALTER COLUMN updated_at SET DEFAULT now()"
    )


def downgrade() -> None:
    for col in [
        "paused_at",
        "frozen_at",
        "last_human_message_at",
        "deleted_at",
        "created_at",
        "updated_at",
    ]:
        op.execute(
            f"ALTER TABLE agent_state_checkpoints "
            f"ALTER COLUMN {col} TYPE TIMESTAMP USING {col} AT TIME ZONE 'UTC'"
        )
