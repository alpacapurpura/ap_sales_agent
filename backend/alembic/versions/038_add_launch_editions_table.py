"""add launch_editions table

Revision ID: 038_add_launch_editions
Revises: 1a34ddb5a7b7
Create Date: 2026-04-09 11:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "038_add_launch_editions"
down_revision: str | None = "1a34ddb5a7b7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS launch_editions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            offer_id UUID NOT NULL REFERENCES products(id),
            tenant_id UUID NOT NULL,
            edition_name VARCHAR NOT NULL,
            edition_number INTEGER NOT NULL,
            start_date TIMESTAMPTZ NOT NULL,
            end_date TIMESTAMPTZ,
            registration_start TIMESTAMPTZ,
            registration_end TIMESTAMPTZ,
            timezone VARCHAR DEFAULT 'UTC',
            pricing_override JSONB,
            capacity INTEGER,
            enrollment_count INTEGER DEFAULT 0,
            status VARCHAR DEFAULT 'draft',
            location_override JSONB,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            CONSTRAINT uq_launch_editions_offer_number UNIQUE (offer_id, edition_number)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_launch_editions_tenant_offer_status
        ON launch_editions (tenant_id, offer_id, status)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_launch_editions_tenant_offer_status")
    op.execute("DROP TABLE IF EXISTS launch_editions")
