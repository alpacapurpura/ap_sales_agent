"""add offer_value_level

Revision ID: a1b2c3d4e5f6
Revises: 6ff69443dd82
Create Date: 2026-02-04 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '6ff69443dd82'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotent: raw SQL with IF NOT EXISTS (per project convention)
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS offer_value_level VARCHAR;")


def downgrade() -> None:
    op.drop_column('products', 'offer_value_level')
