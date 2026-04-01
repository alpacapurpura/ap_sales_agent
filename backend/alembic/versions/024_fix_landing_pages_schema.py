"""Fix landing_pages: add deleted_at, change slug unique to per-tenant.

Revision ID: 024_fix_landing_pages_schema
Revises: 023_commercial_calendar
"""
from alembic import op

revision = "024_fix_landing_pages_schema"
down_revision = "023_commercial_calendar"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add deleted_at column (idempotent)
    op.execute("""
        ALTER TABLE landing_pages
        ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ;
    """)

    # 2. Drop global unique constraint on slug (if it exists)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'landing_pages_slug_key'
                  AND conrelid = 'landing_pages'::regclass
            ) THEN
                ALTER TABLE landing_pages DROP CONSTRAINT landing_pages_slug_key;
            END IF;
        END;
        $$;
    """)

    # 3. Add composite unique index (tenant_id, slug) — idempotent
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_landing_pages_tenant_slug
        ON landing_pages (tenant_id, slug)
        WHERE deleted_at IS NULL;
    """)

    # 4. Ensure index on tenant_id for query performance
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_landing_pages_tenant_id
        ON landing_pages (tenant_id);
    """)

    # 5. Ensure index on deleted_at for soft-delete filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_landing_pages_deleted_at
        ON landing_pages (deleted_at);
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_landing_pages_deleted_at;")
    op.execute("DROP INDEX IF EXISTS ix_landing_pages_tenant_id;")
    op.execute("DROP INDEX IF EXISTS uq_landing_pages_tenant_slug;")
    op.execute("""
        ALTER TABLE landing_pages
        ADD CONSTRAINT landing_pages_slug_key UNIQUE (slug);
    """)
    op.execute("""
        ALTER TABLE landing_pages
        DROP COLUMN IF EXISTS deleted_at;
    """)
