"""add channel_cost_settings table

Revision ID: f5a6b7c8d9e0
Revises: e2f3a4b5c6d7
Create Date: 2026-03-16 03:55:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f5a6b7c8d9e0"
down_revision: str = "e2f3a4b5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS channel_cost_settings (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            channel_slug VARCHAR NOT NULL,
            cost_type VARCHAR NOT NULL,
            monthly_amount FLOAT NOT NULL,
            currency VARCHAR(3) DEFAULT 'USD',
            proration_category VARCHAR,
            description VARCHAR,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ,
            CONSTRAINT uq_channel_cost_tenant_slug_type UNIQUE (tenant_id, channel_slug, cost_type)
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_channel_cost_settings_tenant_id
        ON channel_cost_settings (tenant_id);
    """)


def downgrade() -> None:
    op.drop_table("channel_cost_settings")
