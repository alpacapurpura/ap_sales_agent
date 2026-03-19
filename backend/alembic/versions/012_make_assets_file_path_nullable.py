"""Make assets.file_path nullable and backfill from storage_path.

Revision ID: 012_file_path_nullable
Revises: 011_create_sales
Create Date: 2026-03-19
"""
from alembic import op

# revision identifiers
revision = "012_file_path_nullable"
down_revision = "011_create_sales"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # All operations guarded by IF EXISTS to handle environments where assets table doesn't exist yet
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'assets') THEN
                -- 1. Drop NOT NULL constraint on file_path
                ALTER TABLE assets ALTER COLUMN file_path DROP NOT NULL;

                -- 2. Backfill any existing rows where file_path is NULL but storage_path has a value
                UPDATE assets
                SET file_path = storage_path
                WHERE file_path IS NULL AND storage_path IS NOT NULL;

                -- 3. Set default empty string to prevent future issues from legacy code
                ALTER TABLE assets ALTER COLUMN file_path SET DEFAULT '';
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'assets') THEN
                UPDATE assets
                SET file_path = COALESCE(file_path, storage_path, '')
                WHERE file_path IS NULL;

                ALTER TABLE assets ALTER COLUMN file_path SET NOT NULL;
                ALTER TABLE assets ALTER COLUMN file_path DROP DEFAULT;
            END IF;
        END
        $$;
    """)
