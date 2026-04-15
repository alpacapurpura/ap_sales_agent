"""Merge three heads into single lineage.

Revision ID: 7481ca229b80
Revises: 044_interview_session_hardening, dd3271ee2de4, f86f848caefa
Create Date: 2026-04-15 12:00:00.000000

"""

# revision identifiers, used by Alembic.
revision: str = "7481ca229b80"
down_revision: tuple[str, ...] = (
    "044_interview_session_hardening",
    "dd3271ee2de4",
    "f86f848caefa",
)
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Merge migration — no schema changes."""


def downgrade() -> None:
    """Merge migration — no schema changes."""
