"""Add ``leads.deleted_at`` for soft-delete parity (closes ORM↔DB drift).

Bug origin: ``LeadModel`` declares ``deleted_at = Column(DateTime(timezone=True),
nullable=True, index=True)`` in ``shared/infrastructure/models/crm.py`` but no
migration ever added the column. Result: any ``SELECT`` that loads ``LeadModel``
fails with ``UndefinedColumn: column leads.deleted_at does not exist`` — this
broke ``GET /api/v1/closer-studio/conversations`` (Sales Studio inbox empty for
all tenants).

All operations idempotent (rule ``backend-migrations.md``).

Revision ID: 121_leads_deleted_at
Revises: 120_pi5_copilot_telegram
Create Date: 2026-05-04
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "121_leads_deleted_at"
down_revision = "120_pi5_copilot_telegram"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """All operations idempotent (raw SQL IF NOT EXISTS)."""
    op.execute(
        """
        ALTER TABLE leads
        ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_leads_deleted_at
        ON leads (deleted_at)
        """,
    )


def downgrade() -> None:
    """All operations idempotent."""
    op.execute("DROP INDEX IF EXISTS ix_leads_deleted_at")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS deleted_at")
