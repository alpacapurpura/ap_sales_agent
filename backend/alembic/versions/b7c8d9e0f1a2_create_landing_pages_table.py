"""create landing_pages table and migrate data from products

Revision ID: b7c8d9e0f1a2
Revises: 74ea66958409
Create Date: 2026-03-11 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7c8d9e0f1a2'
down_revision: str = '74ea66958409'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Table already exists (created before migration tracking),
    # so we only migrate data from products.landing_page_config
    conn = op.get_bind()

    # Migrate data using pure SQL - insert from products into landing_pages
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
