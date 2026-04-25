"""copilot: +copilot_pinned_memory (StoreBackend Postgres)

Revision ID: 067_copilot_pinned_memory
Revises: 066_offer_platform_details
Create Date: 2026-04-25

F2 deliverable. Per-user opt-in scratchpad persistence (cross-thread)
distinct from the ephemeral StateBackend used inside a single
conversation. Tool ``pin_to_memory(path)`` (placeholder during F2)
promotes a file from the ephemeral scratchpad to this table.

refs: docs/domains/copilot/redesign-2026-04/02-architecture-target.md §5
"""

from collections.abc import Sequence

from alembic import op

revision: str = "067_copilot_pinned_memory"
down_revision: str | None = "066_offer_platform_details"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Idempotent table + indexes per .claude/rules/backend-migrations.md."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS copilot_pinned_memory (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            user_id UUID NOT NULL,
            path TEXT NOT NULL,
            content TEXT NOT NULL,
            pinned_from_conversation_id UUID NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """,
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_copilot_pinned_memory_tenant_user_path
        ON copilot_pinned_memory (tenant_id, user_id, path)
        """,
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_pinned_memory_tenant
        ON copilot_pinned_memory (tenant_id)
        """,
    )


def downgrade() -> None:
    """Explicit NO-OP. Table is additive; preserve user content on rollback."""
