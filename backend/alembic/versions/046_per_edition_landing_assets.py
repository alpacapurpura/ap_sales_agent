"""per-edition landing and assets (Phase 3)

Binds ``landing_pages`` and ``offer_assets`` to a specific
``launch_editions`` row so each edition owns its own landing content and
asset gallery, while keeping edition-agnostic rows (``edition_id IS NULL``)
as offer-level fallback templates.

Changes:

1. ``landing_pages.edition_id`` — nullable FK to ``launch_editions(id)``.
   ``NOT NULL`` cannot be imposed retroactively without a backfill, and
   offer-level template landings must keep existing rows.
   A partial unique index ``uq_landing_per_offer_edition`` enforces
   one landing per ``(tenant_id, offer_id, edition_id)`` when the edition
   is set; offer-level rows (``edition_id IS NULL``) are excluded and
   continue to rely on the existing ``(tenant, offer)`` unique rule that
   lives outside this migration.
2. ``offer_assets.edition_id`` — nullable FK to ``launch_editions(id)``
   with ``ON DELETE SET NULL`` so dropping an edition demotes its assets
   back to the offer-level pool instead of deleting them.
3. ``offer_assets.shared_across_editions`` — boolean flag that promotes an
   asset to offer-wide visibility even when ``edition_id`` is set. Keeps
   the semantics explicit: an asset scoped to edition X is NOT shared;
   an asset created for edition X but flagged ``shared_across_editions``
   lives in every edition's listing.

All operations idempotent (raw SQL with IF NOT EXISTS / information_schema
guards). FKs use ``NOT VALID`` to avoid validating against live rows on
deploy — they are eventually validated by a follow-up migration once the
backfill script (``scripts/backfill_edition_placeholders.py``) has run.

Revision ID: 046_per_edition_landing_assets
Revises: 045_edition_placeholder
Create Date: 2026-04-17 00:00:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "046_per_edition_landing_assets"
down_revision: str | None = "045_edition_placeholder"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add edition_id to landing_pages + offer_assets, and shared flag."""
    # 1. landing_pages.edition_id
    op.execute(
        """
        ALTER TABLE landing_pages
        ADD COLUMN IF NOT EXISTS edition_id UUID NULL
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_landing_edition'
                  AND table_name = 'landing_pages'
            ) THEN
                ALTER TABLE landing_pages
                ADD CONSTRAINT fk_landing_edition
                FOREIGN KEY (edition_id)
                REFERENCES launch_editions(id)
                ON DELETE CASCADE
                NOT VALID;
            END IF;
        END $$
        """
    )
    # One landing per (tenant, offer, edition) when edition is set. Offer-
    # level rows (edition_id IS NULL) are intentionally excluded — they
    # retain whatever uniqueness rule the landing module already defines.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_landing_per_offer_edition
        ON landing_pages (tenant_id, offer_id, edition_id)
        WHERE deleted_at IS NULL AND edition_id IS NOT NULL
        """
    )
    # Hot-path lookup: "landing for this edition"
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_landing_pages_edition
        ON landing_pages (edition_id)
        WHERE edition_id IS NOT NULL AND deleted_at IS NULL
        """
    )

    # 2. offer_assets.edition_id
    op.execute(
        """
        ALTER TABLE offer_assets
        ADD COLUMN IF NOT EXISTS edition_id UUID NULL
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_asset_edition'
                  AND table_name = 'offer_assets'
            ) THEN
                ALTER TABLE offer_assets
                ADD CONSTRAINT fk_asset_edition
                FOREIGN KEY (edition_id)
                REFERENCES launch_editions(id)
                ON DELETE SET NULL
                NOT VALID;
            END IF;
        END $$
        """
    )

    # 3. offer_assets.shared_across_editions — default FALSE for existing rows.
    op.execute(
        """
        ALTER TABLE offer_assets
        ADD COLUMN IF NOT EXISTS shared_across_editions BOOLEAN NOT NULL DEFAULT FALSE
        """
    )

    # Indexes for the edition-scoped listing hot path.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_offer_assets_edition
        ON offer_assets (tenant_id, offer_id, edition_id)
        WHERE deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_offer_assets_shared
        ON offer_assets (tenant_id, offer_id)
        WHERE deleted_at IS NULL AND shared_across_editions = TRUE
        """
    )


def downgrade() -> None:
    """Best-effort rollback. Assets/landings referencing editions become orphans."""
    op.execute("DROP INDEX IF EXISTS ix_offer_assets_shared")
    op.execute("DROP INDEX IF EXISTS ix_offer_assets_edition")
    op.execute("ALTER TABLE offer_assets DROP CONSTRAINT IF EXISTS fk_asset_edition")
    op.execute("ALTER TABLE offer_assets DROP COLUMN IF EXISTS shared_across_editions")
    op.execute("ALTER TABLE offer_assets DROP COLUMN IF EXISTS edition_id")

    op.execute("DROP INDEX IF EXISTS ix_landing_pages_edition")
    op.execute("DROP INDEX IF EXISTS uq_landing_per_offer_edition")
    op.execute("ALTER TABLE landing_pages DROP CONSTRAINT IF EXISTS fk_landing_edition")
    op.execute("ALTER TABLE landing_pages DROP COLUMN IF EXISTS edition_id")
