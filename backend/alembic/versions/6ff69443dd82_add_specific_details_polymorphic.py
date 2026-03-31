"""add_specific_details_polymorphic

Revision ID: 6ff69443dd82
Revises: 39f437f8196a
Create Date: 2026-02-03 00:13:14.738467

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6ff69443dd82'
down_revision: Union[str, None] = '39f437f8196a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = 'products') THEN
                ALTER TABLE products ADD COLUMN IF NOT EXISTS specific_details JSONB;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS specific_details")
