"""copilot: +brand_summary lighthouse table

Revision ID: 068_brand_summary
Revises: 067_copilot_pinned_memory
Create Date: 2026-04-25

F3 deliverable. Per-tenant living brand summary (≤800 chars, Spanish
neutro) regenerated on ``brand_section_updated`` events. Auto-injected
into the copilot system prompt for routes target (offer-studio,
landing, campaign, sales).

refs: docs/domains/copilot/redesign-2026-04/02-architecture-target.md §4
      docs/domains/copilot/redesign-2026-04/phases/F3-brand-summary-lighthouse.md
"""

from collections.abc import Sequence

from alembic import op

revision: str = "068_brand_summary"
down_revision: str | None = "067_copilot_pinned_memory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Idempotent table per .claude/rules/backend-migrations.md."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS brand_summary (
            tenant_id UUID PRIMARY KEY,
            summary TEXT NOT NULL,
            version INT NOT NULL DEFAULT 1,
            model_used TEXT NOT NULL,
            chars_count INT NOT NULL CHECK (chars_count <= 1000),
            last_section_changed TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
    )


def downgrade() -> None:
    """Explicit NO-OP. Table is additive; preserve summaries on rollback."""
