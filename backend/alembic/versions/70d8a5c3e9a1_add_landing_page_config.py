"""add landing_page_config to products

Revision ID: 70d8a5c3e9a1
Revises: 6ff69443dd82
Create Date: 2026-02-11 12:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '70d8a5c3e9a1'
down_revision = '66a20b0fa0fc' # Corrected previous head
branch_labels = None
depends_on = None

def upgrade():
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = 'products') THEN
                ALTER TABLE products ADD COLUMN IF NOT EXISTS landing_page_config JSONB;
            END IF;
        END $$;
    """)

def downgrade():
    op.execute("""
        ALTER TABLE products
        DROP COLUMN IF EXISTS landing_page_config
    """)
