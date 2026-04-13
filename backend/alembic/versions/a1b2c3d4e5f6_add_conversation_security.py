"""Add conversation security columns (expires_at, deleted_at).

Revision ID: a1b2c3d4e5f6
Revises: f851363921c9
Create Date: 2026-04-13 18:00:00.000000

"""  # noqa: INP001

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "f851363921c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add expires_at and deleted_at to copilot_conversations."""
    # Add expires_at column (nullable for existing rows, defaults to 90 days from now for new)
    op.execute("ALTER TABLE copilot_conversations ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE")

    # Add deleted_at column for soft-delete support
    op.execute("ALTER TABLE copilot_conversations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE")

    # Backfill expires_at for existing rows: created_at + 90 days
    op.execute("UPDATE copilot_conversations SET expires_at = created_at + INTERVAL '90 days' WHERE expires_at IS NULL")

    # Index for efficient cleanup queries
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_copilot_conversations_expires_at "
        "ON copilot_conversations(expires_at) "
        "WHERE deleted_at IS NULL"
    )

    # Index for soft-delete filtering
    op.execute("CREATE INDEX IF NOT EXISTS ix_copilot_conversations_deleted_at ON copilot_conversations(deleted_at)")


def downgrade() -> None:
    """Remove expires_at and deleted_at from copilot_conversations."""
    op.execute("DROP INDEX IF EXISTS ix_copilot_conversations_deleted_at")
    op.execute("DROP INDEX IF EXISTS ix_copilot_conversations_expires_at")
    op.execute("ALTER TABLE copilot_conversations DROP COLUMN IF EXISTS deleted_at")
    op.execute("ALTER TABLE copilot_conversations DROP COLUMN IF EXISTS expires_at")
