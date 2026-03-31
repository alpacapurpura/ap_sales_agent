"""Initial Multitenancy Schema

Revision ID: 16a58268fd71
Revises:
Create Date: 2026-01-27 09:48:31.884936

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '16a58268fd71'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables that the original migration expected to exist.
# Some are orphaned (no SQLAlchemy model) — the DO $$ block skips them safely.
_TENANT_FK_TABLES = [
    'agent_traces',
    'appointments',
    'avatar_definitions',
    'documents',
    'enrollments',
    'llm_call_logs',
    'marketing_assets',
    'messages',
    'objections',
    'offer_logs',
    'products',
    'prompt_versions',
    'sensitive_data',
    'users',
]


def upgrade() -> None:
    # 1. Create tenants table
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id   UUID PRIMARY KEY,
            name VARCHAR NOT NULL,
            slug VARCHAR NOT NULL,
            config_json JSONB,
            is_active   BOOLEAN DEFAULT TRUE,
            created_at  TIMESTAMPTZ DEFAULT now(),
            updated_at  TIMESTAMPTZ
        )
    """)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_tenants_slug ON tenants (slug)"
    )

    # 2. Add tenant_id to every legacy table (skip if table doesn't exist)
    for table in _TENANT_FK_TABLES:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = '{table}'
                ) THEN
                    ALTER TABLE {table} ADD COLUMN IF NOT EXISTS tenant_id UUID;
                END IF;
            END $$
        """)

    # 3. Foreign keys (skip if table or column missing)
    for table in _TENANT_FK_TABLES:
        fk_name = f"fk_{table}_tenant_id"
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name  = '{table}'
                      AND column_name = 'tenant_id'
                ) AND NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = '{fk_name}'
                      AND table_name = '{table}'
                ) THEN
                    ALTER TABLE {table}
                        ADD CONSTRAINT {fk_name}
                        FOREIGN KEY (tenant_id) REFERENCES tenants(id);
                END IF;
            END $$
        """)

    # 4. users.custom_system_instruction type change (VARCHAR ↔ TEXT are equivalent in PG, safe no-op)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name  = 'users'
                  AND column_name = 'custom_system_instruction'
            ) THEN
                ALTER TABLE users
                    ALTER COLUMN custom_system_instruction TYPE VARCHAR;
            END IF;
        END $$
    """)


def downgrade() -> None:
    for table in reversed(_TENANT_FK_TABLES):
        fk_name = f"fk_{table}_tenant_id"
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = '{fk_name}'
                ) THEN
                    ALTER TABLE {table} DROP CONSTRAINT {fk_name};
                END IF;
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = '{table}' AND column_name = 'tenant_id'
                ) THEN
                    ALTER TABLE {table} DROP COLUMN tenant_id;
                END IF;
            END $$
        """)
    op.execute("DROP INDEX IF EXISTS ix_tenants_slug")
    op.execute("DROP TABLE IF EXISTS tenants")
