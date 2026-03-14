"""fix_products_schema_timestamps

Revision ID: 94469ab70585
Revises: 3d6ac283c93d
Create Date: 2026-02-25 18:25:52.329872

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '94469ab70585'
down_revision: Union[str, None] = '3d6ac283c93d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use ADD COLUMN IF NOT EXISTS to be safe against already-applied schema changes
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS marketing_pain_points JSONB")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS marketing_desires JSONB")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS support_duration_days INTEGER")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS onboarding_action VARCHAR")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS onboarding_url VARCHAR")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS calendar_type_id VARCHAR")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS checkout_page_url VARCHAR")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS vsl_link VARCHAR")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now()")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE")


def downgrade() -> None:
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS updated_at')
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS created_at')
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS vsl_link')
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS checkout_page_url')
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS calendar_type_id')
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS onboarding_url')
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS onboarding_action')
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS support_duration_days')
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS marketing_desires')
    op.execute('ALTER TABLE products DROP COLUMN IF EXISTS marketing_pain_points')
