"""Add idempotent natural-key partial unique index on copilot_mutation_journal.

Natural key for active rows = (tenant_id, conversation_id, message_id, field_path)
WHERE reverted_at IS NULL. Lets ``MutationApplyService`` retry safely without
inserting duplicate journal rows when ``ProposalCard`` falls back from the
form-runtime bridge to the backend ``/mutations/apply`` endpoint (B22-FP1 AC5).

Idempotent — uses raw SQL ``CREATE UNIQUE INDEX IF NOT EXISTS``.

Revision ID: 074_mutation_journal_natural_key_idempotent
Revises: 073_add_chinese_provider_keys
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "074_mutation_journal_natural_key_idempotent"
down_revision: str | None = "073_add_chinese_provider_keys"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create partial unique index for active mutation rows."""
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
        ux_copilot_mutation_journal_active_natural_key
        ON copilot_mutation_journal (
            tenant_id,
            conversation_id,
            message_id,
            field_path
        )
        WHERE reverted_at IS NULL
        """,
    )


def downgrade() -> None:
    """Drop the partial unique index."""
    op.execute(
        "DROP INDEX IF EXISTS ux_copilot_mutation_journal_active_natural_key",
    )
