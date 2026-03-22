"""add offer_value_level

Revision ID: a1b2c3d4e5f6
Revises: 9c6fc3c2980b
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
    # Add the new column offer_value_level
    op.add_column('products', sa.Column('offer_value_level', sa.String(), nullable=True))
    
    # Note: JSONB fields (pricing, specific_details, prerequisites) are already there 
    # and schema-less, so no migration needed for them unless we want to migrate data inside them.


def downgrade() -> None:
    op.drop_column('products', 'offer_value_level')
