"""Add deleted_at column to commercial_calendar_events for soft delete.

Revision ID: 034_deleted_at_calendar
Revises: 033_add_period_aware_columns
Create Date: 2026-04-04
"""
from alembic import op

revision = "034_deleted_at_calendar"
down_revision = "035_appointments_schema_sync"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE commercial_calendar_events "
        "ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ DEFAULT NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_cal_deleted_at "
        "ON commercial_calendar_events (deleted_at)"
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_cal_deleted_at")
    op.execute(
        "ALTER TABLE commercial_calendar_events "
        "DROP COLUMN IF EXISTS deleted_at"
    )
