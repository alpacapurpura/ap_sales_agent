"""Fix appointments tenant_id: add column, index, and backfill.

The initial multitenancy migration (16a58268fd71) wrapped the ADD COLUMN
in a DO $$ / IF EXISTS(table) block that succeeded but silently skipped
the column when the appointments table didn't exist yet at that point.
This migration ensures the column, index, and backfill are applied
idempotently.

Revision ID: 028_fix_appointments_tenant_id
Revises: 027_add_sub_extractor_failures
"""

from alembic import op

revision = "028_fix_appointments_tenant_id"
down_revision = "027_add_sub_extractor_failures"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Guard: skip entirely if the appointments table doesn't exist yet
    # (fresh DB where the table is created by a later migration)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'appointments'
            ) THEN
                -- 1. Add tenant_id column if missing
                ALTER TABLE appointments
                ADD COLUMN IF NOT EXISTS tenant_id UUID;

                -- 2. Create index for tenant_id lookups
                CREATE INDEX IF NOT EXISTS ix_appointments_tenant_id
                ON appointments (tenant_id);

                -- 3. Backfill existing rows with the known production tenant ID
                UPDATE appointments
                SET tenant_id = '9831cfbe-3912-429e-a944-40f3e7bf1372'
                WHERE tenant_id IS NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_appointments_tenant_id;")
    op.execute("ALTER TABLE appointments DROP COLUMN IF EXISTS tenant_id;")
