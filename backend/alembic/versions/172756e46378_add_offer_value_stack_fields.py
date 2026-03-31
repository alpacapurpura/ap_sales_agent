"""add_offer_value_stack_fields

Revision ID: 172756e46378
Revises: 9c6fc3c2980b
Create Date: 2026-02-02 22:19:56.663126

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '172756e46378'
down_revision: Union[str, None] = '9c6fc3c2980b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = 'products') THEN
                ALTER TABLE products ADD COLUMN IF NOT EXISTS primary_outcome VARCHAR;
                ALTER TABLE products ADD COLUMN IF NOT EXISTS time_to_value VARCHAR;
                ALTER TABLE products ADD COLUMN IF NOT EXISTS prerequisites JSONB;
                ALTER TABLE products ADD COLUMN IF NOT EXISTS guarantee_terms TEXT;
                ALTER TABLE products ADD COLUMN IF NOT EXISTS includes_offers JSONB;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS includes_offers")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS guarantee_terms")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS prerequisites")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS time_to_value")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS primary_outcome")
