"""add_offer_id_to_gallery_images

Revision ID: 3d6ac283c93d
Revises: 8bd6b013a46e
Create Date: 2026-02-25 16:58:02.214550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = '3d6ac283c93d'
down_revision: Union[str, None] = '8bd6b013a46e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    if 'gallery_images' not in existing_tables:
        print("Skipping: gallery_images table does not exist")
        return

    columns = [c['name'] for c in inspector.get_columns('gallery_images')]
    if 'offer_id' not in columns:
        op.add_column('gallery_images', sa.Column('offer_id', sa.UUID(), nullable=True))

    op.execute('CREATE INDEX IF NOT EXISTS ix_gallery_images_offer_id ON gallery_images (offer_id)')

    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_gallery_images_offer_id'
            ) THEN
                ALTER TABLE gallery_images ADD CONSTRAINT fk_gallery_images_offer_id
                FOREIGN KEY (offer_id) REFERENCES products(id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_gallery_images_offer_id'
            ) THEN
                ALTER TABLE gallery_images DROP CONSTRAINT fk_gallery_images_offer_id;
            END IF;
        END $$;
    """)
    op.execute('DROP INDEX IF EXISTS ix_gallery_images_offer_id')
    op.execute('ALTER TABLE gallery_images DROP COLUMN IF EXISTS offer_id')
