"""Add is_active column to user_tenants for per-tenant soft-delete.

Allows removing a user from a specific tenant without affecting their
global account or other tenant memberships.

Revision ID: 016_user_tenant_soft_delete
Revises: 015_email_slugs
Create Date: 2026-03-26
"""
from alembic import op

# revision identifiers
revision = "016_user_tenant_soft_delete"
down_revision = "015_email_slugs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE user_tenants ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true NOT NULL"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE user_tenants DROP COLUMN IF EXISTS is_active")
