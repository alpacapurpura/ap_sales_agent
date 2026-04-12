"""add_interview_sessions

Revision ID: 3dbcf9737aa6
Revises: 043_add_has_editions
Create Date: 2026-04-12 18:18:31.027515

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3dbcf9737aa6"
down_revision: str | None = "043_add_has_editions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            domain VARCHAR(50) NOT NULL DEFAULT 'brand',
            config_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
            conversation_id UUID REFERENCES copilot_conversations(id) ON DELETE SET NULL,
            mapa_global JSONB NOT NULL DEFAULT '{}'::jsonb,
            bloque_actual VARCHAR(100) NOT NULL DEFAULT '',
            bloques_completados JSONB NOT NULL DEFAULT '[]'::jsonb,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            messages_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_interview_sessions_tenant_id
        ON interview_sessions (tenant_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_interview_sessions_tenant_domain_status
        ON interview_sessions (tenant_id, domain)
        WHERE status = 'active' AND deleted_at IS NULL;
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_interview_sessions_one_active_per_domain
        ON interview_sessions (tenant_id, domain)
        WHERE status = 'active' AND deleted_at IS NULL;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS interview_sessions;")
