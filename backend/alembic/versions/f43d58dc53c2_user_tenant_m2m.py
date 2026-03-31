"""user_tenant_m2m

Revision ID: f43d58dc53c2
Revises: 28260b11b4aa
Create Date: 2026-02-17 02:10:54.107128

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f43d58dc53c2'
down_revision: Union[str, None] = '28260b11b4aa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create user_tenants table (idempotent)
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_tenants (
            user_id UUID NOT NULL,
            tenant_id UUID NOT NULL,
            role VARCHAR,
            created_at TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (user_id, tenant_id),
            CONSTRAINT fk_user_tenants_user FOREIGN KEY (user_id) REFERENCES users(id),
            CONSTRAINT fk_user_tenants_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id)
        )
    """)

    # 2. Data migration: Copy existing user-tenant relationships
    #    Only if users.tenant_id column exists (won't exist on fresh DB)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'tenant_id'
            ) THEN
                INSERT INTO user_tenants (user_id, tenant_id, role, created_at)
                SELECT id, tenant_id, 'admin', NOW()
                FROM users
                WHERE tenant_id IS NOT NULL
                ON CONFLICT (user_id, tenant_id) DO NOTHING;
            END IF;
        END $$
    """)

    # 3. Drop old constraints (idempotent)
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS uq_user_email_tenant")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS uq_users_email_tenant")

    # 4. Add unique constraint on email (idempotent)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conrelid = 'users'::regclass
                  AND contype = 'u'
                  AND array_length(conkey, 1) = 1
                  AND conkey[1] = (
                      SELECT attnum FROM pg_attribute
                      WHERE attrelid = 'users'::regclass AND attname = 'email'
                  )
            ) THEN
                ALTER TABLE users ADD CONSTRAINT uq_users_email UNIQUE (email);
            END IF;
        END $$
    """)

    # 5. Drop old tenant_id FK and column from users (idempotent)
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_tenant_id_fkey1")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_tenant_id_fkey")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS tenant_id")


def downgrade() -> None:
    # 1. Re-add tenant_id column to users (idempotent)
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS tenant_id UUID")

    # 2. Add FK constraint (idempotent)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'users_tenant_id_fkey1'
            ) THEN
                ALTER TABLE users ADD CONSTRAINT users_tenant_id_fkey1
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id);
            END IF;
        END $$
    """)

    # 3. Drop the email-only unique constraint (idempotent)
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS uq_users_email")

    # 4. Re-add compound unique constraint (idempotent)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_user_email_tenant'
            ) THEN
                ALTER TABLE users ADD CONSTRAINT uq_user_email_tenant UNIQUE (email, tenant_id);
            END IF;
        END $$
    """)

    # 5. Backfill users.tenant_id from user_tenants
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'user_tenants'
            ) THEN
                UPDATE users u SET tenant_id = ut.tenant_id
                FROM user_tenants ut
                WHERE u.id = ut.user_id AND u.tenant_id IS NULL;
            END IF;
        END $$
    """)

    # 6. Drop user_tenants table
    op.execute("DROP TABLE IF EXISTS user_tenants")
