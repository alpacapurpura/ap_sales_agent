"""Add sub_extractor_failures JSONB column to extraction_runs.

Revision ID: 027_add_sub_extractor_failures
Revises: 026_add_tracking_config_to_tenants
"""

from alembic import op

revision = "027_add_sub_extractor_failures"
down_revision = "026_add_tracking_config_to_tenants"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE extraction_runs
        ADD COLUMN IF NOT EXISTS sub_extractor_failures JSONB DEFAULT '[]'::jsonb;
    """)


def downgrade() -> None:
    op.execute(
        "ALTER TABLE extraction_runs DROP COLUMN IF EXISTS sub_extractor_failures;"
    )
