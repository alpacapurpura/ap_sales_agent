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
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS default_currency VARCHAR DEFAULT 'USD'")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS timezone VARCHAR DEFAULT 'UTC'")


def downgrade() -> None:
    op.execute('ALTER TABLE tenants DROP COLUMN IF EXISTS timezone')
    op.execute('ALTER TABLE tenants DROP COLUMN IF EXISTS default_currency')
