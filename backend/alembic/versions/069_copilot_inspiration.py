"""copilot: +copilot_inspiration table (F4 url contextual + scratchpad)

Revision ID: 069_copilot_inspiration
Revises: 068_brand_summary
Create Date: 2026-04-25

F4 deliverable. Per-conversation URL-as-inspiration persistence.
Stores extracted markdown summary + sub-elements + brand_relevance_score
so the inspirations table fragment can rebuild from DB on every turn
(survives conversation rehydration, unlike deepagents StateBackend).

refs: docs/domains/copilot/redesign-2026-04/02-architecture-target.md §5
      docs/domains/copilot/redesign-2026-04/phases/F4-url-contextual-scratchpad.md
"""

from collections.abc import Sequence

from alembic import op

revision: str = "069_copilot_inspiration"
down_revision: str | None = "068_brand_summary"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Idempotent table per .claude/rules/backend-migrations.md."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS copilot_inspiration (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            conversation_id UUID NOT NULL,
            slug TEXT NOT NULL,
            url TEXT NOT NULL,
            why TEXT NOT NULL DEFAULT '',
            domain TEXT NOT NULL,
            title TEXT NULL,
            summary TEXT NOT NULL,
            sub_elements JSONB NOT NULL DEFAULT '{}'::jsonb,
            brand_relevance_score NUMERIC(3,2) NOT NULL DEFAULT 0.5,
            content_md TEXT NOT NULL,
            og_image TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_copilot_inspiration_conversation_slug
                UNIQUE (conversation_id, slug)
        )
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_inspiration_conv_created
        ON copilot_inspiration (conversation_id, created_at DESC)
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_inspiration_tenant
        ON copilot_inspiration (tenant_id)
        """,
    )


def downgrade() -> None:
    """Explicit NO-OP. Table is additive; preserve inspirations on rollback."""
