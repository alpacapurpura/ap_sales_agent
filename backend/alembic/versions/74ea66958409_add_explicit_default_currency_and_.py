"""Add explicit default_currency and timezone to tenants

Revision ID: 74ea66958409
Revises: 194925304af0
Create Date: 2026-03-04 01:34:49.120233

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '74ea66958409'
down_revision: Union[str, None] = '194925304af0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tenants', sa.Column('default_currency', sa.String(), server_default='USD', nullable=True))
    op.add_column('tenants', sa.Column('timezone', sa.String(), server_default='UTC', nullable=True))


def downgrade() -> None:
    op.drop_column('tenants', 'timezone')
    op.drop_column('tenants', 'default_currency')
