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
    # 1. Drop NOT NULL constraint on file_path (idempotent: safe to run if already nullable)
    op.execute("ALTER TABLE assets ALTER COLUMN file_path DROP NOT NULL;")

    # 2. Backfill any existing rows where file_path is NULL but storage_path has a value
    op.execute("""
        UPDATE assets
        SET file_path = storage_path
        WHERE file_path IS NULL AND storage_path IS NOT NULL;
    """)

    # 3. Set default empty string to prevent future issues from legacy code
    op.execute("ALTER TABLE assets ALTER COLUMN file_path SET DEFAULT '';")


def downgrade() -> None:
    # Backfill NULLs before re-adding NOT NULL constraint
    op.execute("""
        UPDATE assets
        SET file_path = COALESCE(file_path, storage_path, '')
        WHERE file_path IS NULL;
    """)
    op.execute("ALTER TABLE assets ALTER COLUMN file_path SET NOT NULL;")
    op.execute("ALTER TABLE assets ALTER COLUMN file_path DROP DEFAULT;")
