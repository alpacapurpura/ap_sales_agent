"""create landing_pages table and migrate data from products

Revision ID: b7c8d9e0f1a2
Revises: 74ea66958409
Create Date: 2026-03-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: str = '74ea66958409'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if 'landing_pages' not in existing_tables:
        print("Skipping data migration: landing_pages table does not exist")
        return

    if 'products' not in existing_tables:
        print("Skipping data migration: products table does not exist")
        return

    products_cols = [c['name'] for c in inspector.get_columns('products')]
    if 'landing_page_config' not in products_cols:
        print("Skipping data migration: products.landing_page_config column does not exist")
        return

    conn.execute(sa.text("""
        INSERT INTO landing_pages (id, tenant_id, offer_id, slug, config, is_published, created_at)
        SELECT
            gen_random_uuid(),
            p.tenant_id,
            p.id,
            CASE
                WHEN p.landing_page_config->>'slug' LIKE '/p/%%'
                    THEN substring(p.landing_page_config->>'slug' from 4)
                WHEN p.landing_page_config->>'slug' LIKE '/%%'
                    THEN substring(p.landing_page_config->>'slug' from 2)
                ELSE COALESCE(p.landing_page_config->>'slug', 'offer-' || left(p.id::text, 8))
            END,
            p.landing_page_config,
            false,
            now()
        FROM products p
        WHERE p.landing_page_config IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM landing_pages lp WHERE lp.offer_id = p.id
          )
    """))


def downgrade() -> None:
    op.execute("DELETE FROM landing_pages")
