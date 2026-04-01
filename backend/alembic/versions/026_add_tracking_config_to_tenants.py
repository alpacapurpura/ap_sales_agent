"""Add tracking_config column to tenants table.

Revision ID: 026_add_tracking_config_to_tenants
Revises: 025_create_tenant_domains
"""
from alembic import op

revision = "026_add_tracking_config_to_tenants"
down_revision = "025_create_tenant_domains"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Widen alembic_version.version_num to support revision IDs longer than 32 chars.
    # Fresh installs create VARCHAR(32); prod DB was created with VARCHAR(128).
    op.execute("""
        ALTER TABLE alembic_version
        ALTER COLUMN version_num TYPE VARCHAR(128);
    """)

    op.execute("""
        ALTER TABLE tenants
        ADD COLUMN IF NOT EXISTS tracking_config JSONB DEFAULT '{}'::jsonb;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS tracking_config;")
