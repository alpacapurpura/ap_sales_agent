"""edition placeholder lifecycle (Phase 2)

Prepares ``launch_editions`` for the placeholder-on-offer-creation flow:

1. ``start_date`` becomes nullable so a brand-new offer can spawn a DRAFT
   placeholder edition without a date. Domain validators ensure that
   transitions to UPCOMING / ACTIVE / PUBLIC still require a date.
2. New ``visibility`` column — editions default to PRIVATE, gating them
   from sales-agent discovery until the user explicitly publishes.
3. New ``cloned_from_edition_id`` column — traceability for the
   clone-with-evolution flow landing in Phase 3.

All operations idempotent (raw SQL with IF EXISTS / IF NOT EXISTS).

Revision ID: 045_edition_placeholder
Revises: 7481ca229b80
Create Date: 2026-04-17 00:00:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "045_edition_placeholder"
down_revision: str | None = "7481ca229b80"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Relax ``start_date`` + add ``visibility`` and ``cloned_from_edition_id``."""
    # 1. Relax NOT NULL on start_date (placeholder editions have no date yet).
    op.execute(
        """
        ALTER TABLE launch_editions
        ALTER COLUMN start_date DROP NOT NULL
        """
    )

    # 2. Add visibility column with PRIVATE default for existing rows.
    #    'private' | 'public'. Only PUBLIC editions are visible to the
    #    sales agent and to public landing URLs.
    op.execute(
        """
        ALTER TABLE launch_editions
        ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) NOT NULL DEFAULT 'private'
        """
    )

    # 3. Add cloned_from_edition_id FK for clone-with-evolution provenance.
    op.execute(
        """
        ALTER TABLE launch_editions
        ADD COLUMN IF NOT EXISTS cloned_from_edition_id UUID NULL
        """
    )
    # FK uses NOT VALID to avoid validating against live data on deploy;
    # the FK is eventually validated by a follow-up migration once backfilled.
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_edition_cloned_from'
                  AND table_name = 'launch_editions'
            ) THEN
                ALTER TABLE launch_editions
                ADD CONSTRAINT fk_edition_cloned_from
                FOREIGN KEY (cloned_from_edition_id)
                REFERENCES launch_editions(id)
                ON DELETE SET NULL
                NOT VALID;
            END IF;
        END $$
        """
    )

    # 4. Index to support future queries like "who cloned from this edition?".
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_launch_editions_cloned_from
        ON launch_editions (cloned_from_edition_id)
        WHERE cloned_from_edition_id IS NOT NULL
        """
    )

    # 5. Index to support "list public editions for offer X" — hot path for
    #    the sales agent's list_public_editions tool (Phase 6).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_launch_editions_public_by_offer
        ON launch_editions (offer_id, status, start_date)
        WHERE visibility = 'public'
        """
    )


def downgrade() -> None:
    """Best-effort rollback. Cannot re-impose NOT NULL on start_date if any row is null."""
    op.execute("DROP INDEX IF EXISTS ix_launch_editions_public_by_offer")
    op.execute("DROP INDEX IF EXISTS ix_launch_editions_cloned_from")
    op.execute("ALTER TABLE launch_editions DROP CONSTRAINT IF EXISTS fk_edition_cloned_from")
    op.execute("ALTER TABLE launch_editions DROP COLUMN IF EXISTS cloned_from_edition_id")
    op.execute("ALTER TABLE launch_editions DROP COLUMN IF EXISTS visibility")
    # NOTE: intentionally not restoring NOT NULL on start_date — rollback would
    # fail if any placeholder editions exist. Operators should backfill and
    # manually add the constraint if they truly need to roll back.
