"""copilot refactor v2: summary metadata, routing log, mutation journal, plan state.

Revision ID: 055_copilot_refactor_v2
Revises: 054_create_social_proof
Create Date: 2026-04-21 12:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "055_copilot_refactor_v2"
down_revision: str | None = "054_create_social_proof"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add v2 columns + routing_log + mutation_journal tables (idempotent)."""
    # ── ALTER copilot_conversations (idempotent per-column) ──────────────
    op.execute("ALTER TABLE copilot_conversations ADD COLUMN IF NOT EXISTS summary_updated_at TIMESTAMPTZ")
    op.execute("ALTER TABLE copilot_conversations ADD COLUMN IF NOT EXISTS summary_dirty_at TIMESTAMPTZ")
    op.execute("ALTER TABLE copilot_conversations ADD COLUMN IF NOT EXISTS message_count INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE copilot_conversations ADD COLUMN IF NOT EXISTS total_tokens INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE copilot_conversations ADD COLUMN IF NOT EXISTS last_tier_used TEXT")
    op.execute(
        "ALTER TABLE copilot_conversations ADD COLUMN IF NOT EXISTS title_auto_generated BOOLEAN NOT NULL DEFAULT false"
    )
    op.execute("ALTER TABLE copilot_conversations ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ")
    op.execute("ALTER TABLE copilot_conversations ADD COLUMN IF NOT EXISTS procedure_id UUID")
    op.execute("ALTER TABLE copilot_conversations ADD COLUMN IF NOT EXISTS procedure_state JSONB")
    op.execute("ALTER TABLE copilot_conversations ADD COLUMN IF NOT EXISTS plan_state JSONB")

    # Partial index for efficient sidebar queries (active conversations only)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_conv_tenant_user_active
          ON copilot_conversations (tenant_id, user_id, updated_at DESC)
          WHERE archived_at IS NULL
        """
    )

    # Partial index for background summarization worker
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_conv_summary_dirty
          ON copilot_conversations (summary_dirty_at)
          WHERE summary_dirty_at IS NOT NULL
        """
    )

    # ── copilot_routing_log ──────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS copilot_routing_log (
            id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID         NOT NULL,
            conversation_id UUID         NOT NULL,
            message_id      UUID         NOT NULL,
            tier_selected   TEXT         NOT NULL,
            classifier_used TEXT         NOT NULL,
            reason          TEXT         NOT NULL,
            confidence      NUMERIC(4,3) NULL,
            user_msg_length INTEGER      NOT NULL,
            tools_available INTEGER      NOT NULL,
            created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_routing_log_tenant_time
          ON copilot_routing_log (tenant_id, created_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_routing_log_conv
          ON copilot_routing_log (conversation_id, created_at DESC)
        """
    )

    # ── copilot_mutation_journal ─────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS copilot_mutation_journal (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID        NOT NULL,
            conversation_id UUID        NOT NULL,
            message_id      UUID        NOT NULL,
            domain          TEXT        NOT NULL,
            entity_id       UUID        NULL,
            field_path      TEXT        NOT NULL,
            old_value       JSONB       NULL,
            new_value       JSONB       NULL,
            applied_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            reverted_at     TIMESTAMPTZ NULL
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_mutation_journal_conv_time
          ON copilot_mutation_journal (conversation_id, applied_at DESC)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_mutation_journal_tenant_active
          ON copilot_mutation_journal (tenant_id, applied_at DESC)
          WHERE reverted_at IS NULL
        """
    )


def downgrade() -> None:
    """Drop the two new tables and the added indexes/columns."""
    op.execute("DROP TABLE IF EXISTS copilot_mutation_journal")
    op.execute("DROP TABLE IF EXISTS copilot_routing_log")

    op.execute("DROP INDEX IF EXISTS ix_copilot_conv_summary_dirty")
    op.execute("DROP INDEX IF EXISTS ix_copilot_conv_tenant_user_active")

    for col in (
        "plan_state",
        "procedure_state",
        "procedure_id",
        "archived_at",
        "title_auto_generated",
        "last_tier_used",
        "total_tokens",
        "message_count",
        "summary_dirty_at",
        "summary_updated_at",
    ):
        op.execute(f"ALTER TABLE copilot_conversations DROP COLUMN IF EXISTS {col}")
