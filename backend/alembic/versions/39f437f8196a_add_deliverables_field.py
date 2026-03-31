"""add_deliverables_field

Revision ID: 39f437f8196a
Revises: 172756e46378
Create Date: 2026-02-02 22:22:25.011760

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '39f437f8196a'
down_revision: Union[str, None] = '172756e46378'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = 'products') THEN
                ALTER TABLE products ADD COLUMN IF NOT EXISTS deliverables JSONB;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS deliverables")
