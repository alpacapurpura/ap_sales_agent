"""copilot blocks backfill marker (PR-3 PI-2 S1).

Marker revision documenting that as of this revision, the canonical state
is "all messages MUST carry blocks". The actual backfill runs as a
separate script:

    backend/scripts/backfill_copilot_content_to_blocks.py

Idempotent: this migration writes nothing data-wise. It exists only so that:
- alembic history shows the cutover point
- the backfill script can stamp a marker row in copilot_backfill_runs
  (created here, IF NOT EXISTS) for resume + audit trail

Run order (post-deploy):
1. ``alembic upgrade head``  — creates copilot_backfill_runs table (this file)
2. ``python scripts/backfill_copilot_content_to_blocks.py --dry-run``  — preview
3. ``python scripts/backfill_copilot_content_to_blocks.py --apply``    — persist
4. Verify: ``SELECT COUNT(*) FROM copilot_conversations
            WHERE messages::jsonb @? '$[*] ? (!exists(@.blocks))'`` → 0

Revision ID: 111_copilot_blocks_backfill_marker
Revises: 110_billing_compliance_tables
Create Date: 2026-04-29
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "111_copilot_blocks_backfill_marker"
down_revision: str | None = "110_billing_compliance_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create audit table for backfill runs (idempotent raw SQL)."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS copilot_backfill_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id UUID NOT NULL,
            tenant_id UUID NULL,
            started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            ended_at TIMESTAMPTZ NULL,
            mode TEXT NOT NULL CHECK (mode IN ('dry_run', 'apply')),
            convs_scanned INT NOT NULL DEFAULT 0,
            convs_updated INT NOT NULL DEFAULT 0,
            msgs_legacy_converted INT NOT NULL DEFAULT 0,
            convs_skipped_corrupt INT NOT NULL DEFAULT 0,
            failed_conv_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            status TEXT NOT NULL CHECK (
                status IN ('running', 'completed', 'aborted', 'failed')
            ),
            error_message TEXT NULL,
            git_sha TEXT NULL
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_backfill_runs_run_id
            ON copilot_backfill_runs (run_id)
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_copilot_backfill_runs_tenant_started
            ON copilot_backfill_runs (tenant_id, started_at DESC)
            WHERE tenant_id IS NOT NULL
        """
    )


def downgrade() -> None:
    """Reverse: drop indexes + table (idempotent)."""
    op.execute("DROP INDEX IF EXISTS ix_copilot_backfill_runs_tenant_started")
    op.execute("DROP INDEX IF EXISTS ix_copilot_backfill_runs_run_id")
    op.execute("DROP TABLE IF EXISTS copilot_backfill_runs")
