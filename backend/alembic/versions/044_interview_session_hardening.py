# ruff: noqa: INP001
"""Interview session hardening: entity_id column + unique partial index.

Revision ID: 044_interview_session_hardening
Revises: f851363921c9
Create Date: 2026-04-13 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "044_interview_session_hardening"
down_revision: str | None = "f851363921c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add entity_id column and ensure unique partial index for active sessions."""
    # Add entity_id column (missing from original migration 3dbcf9737aa6)
    op.execute("""
        ALTER TABLE interview_sessions
        ADD COLUMN IF NOT EXISTS entity_id UUID;
    """)

    # Safety net: ensure the unique partial index exists
    # (was already created in 3dbcf9737aa6, but IF NOT EXISTS is idempotent)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_interview_sessions_one_active_per_domain
        ON interview_sessions (tenant_id, domain)
        WHERE status = 'active' AND deleted_at IS NULL;
    """)


def downgrade() -> None:
    """Remove entity_id column."""
    op.execute("""
        ALTER TABLE interview_sessions
        DROP COLUMN IF EXISTS entity_id;
    """)
