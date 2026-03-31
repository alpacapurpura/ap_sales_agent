"""add_clerk_id_to_users

Revision ID: d25f28231eee
Revises: 70d8a5c3e9a1
Create Date: 2026-02-15 01:32:22.480057

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd25f28231eee'
down_revision: Union[str, None] = '70d8a5c3e9a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = 'users') THEN
                ALTER TABLE users ADD COLUMN IF NOT EXISTS clerk_id VARCHAR;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_schema = 'public' AND table_name = 'users'
                         AND column_name = 'clerk_id') THEN
                CREATE UNIQUE INDEX IF NOT EXISTS ix_users_clerk_id ON users (clerk_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DROP INDEX IF EXISTS ix_users_clerk_id
    """)
    op.execute("""
        ALTER TABLE users
        DROP COLUMN IF EXISTS clerk_id
    """)
