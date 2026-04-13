"""add_buyer_personas

Revision ID: f851363921c9
Revises: 3dbcf9737aa6
Create Date: 2026-04-13 03:16:30.307429

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f851363921c9"
down_revision: str | None = "3dbcf9737aa6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS buyer_personas (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            user_id UUID NOT NULL,
            name VARCHAR(255) NOT NULL,
            tagline TEXT,
            scope VARCHAR(20) NOT NULL DEFAULT 'GLOBAL',
            offer_id UUID,
            is_primary BOOLEAN NOT NULL DEFAULT FALSE,
            demographics JSONB NOT NULL DEFAULT '{}',
            psychographics JSONB NOT NULL DEFAULT '{}',
            pain_points JSONB NOT NULL DEFAULT '[]',
            desires JSONB NOT NULL DEFAULT '[]',
            objections JSONB NOT NULL DEFAULT '[]',
            preferred_channels JSONB NOT NULL DEFAULT '[]',
            buyer_journey JSONB NOT NULL DEFAULT '{}',
            purchase_triggers JSONB NOT NULL DEFAULT '[]',
            anti_patterns JSONB NOT NULL DEFAULT '[]',
            completeness_score FLOAT NOT NULL DEFAULT 0.0,
            interview_session_id UUID,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            deleted_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_buyer_personas_tenant_id "
        "ON buyer_personas(tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_buyer_personas_tenant_scope "
        "ON buyer_personas(tenant_id, scope)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_buyer_personas_tenant_scope")
    op.execute("DROP INDEX IF EXISTS ix_buyer_personas_tenant_id")
    op.execute("DROP TABLE IF EXISTS buyer_personas")
