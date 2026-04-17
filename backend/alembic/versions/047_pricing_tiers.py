"""temporal pricing tiers (Phase 4)

Adds ``launch_editions.pricing_tiers`` (JSONB) and one-shot data-migrates
the legacy ``pricing_override`` list into a single ``regular`` tier with
open-ended validity (``valid_from = valid_until = NULL``).

The ``pricing_override`` column is kept in place for one release so any
in-flight deployment can still read it. A follow-up migration (048) will
drop it once the new read path is rolled out.

Idempotency notes:

- ``ADD COLUMN IF NOT EXISTS`` covers column creation.
- The data migration checks ``pricing_tiers IS NULL`` so re-running after
  a partial failure is a no-op.
- No ``UPDATE`` runs when ``pricing_override`` is already ``NULL`` —
  editions created under the new regime land with ``pricing_tiers``
  populated directly by the service layer.

Revision ID: 047_pricing_tiers
Revises: 046_per_edition_landing_assets
Create Date: 2026-04-17 01:30:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "047_pricing_tiers"
down_revision: str | None = "046_per_edition_landing_assets"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add ``pricing_tiers`` column + backfill from ``pricing_override``."""
    op.execute(
        """
        ALTER TABLE launch_editions
        ADD COLUMN IF NOT EXISTS pricing_tiers JSONB NULL
        """
    )

    # One-shot data migration — every existing pricing_override entry
    # becomes an element of a single ``regular`` tier with open-ended
    # windows. We aggregate inside a subquery so editions with multiple
    # plan rows produce a single tier whose ``pricing`` holds the list.
    #
    # Guardrails:
    # - ``pricing_tiers IS NULL``: skip editions that already ran.
    # - ``pricing_override IS NOT NULL``: nothing to copy otherwise.
    # - ``jsonb_typeof() = 'array'``: defensive — older rows with stray
    #   non-array JSON should not crash the migration.
    op.execute(
        """
        UPDATE launch_editions AS le
        SET pricing_tiers = jsonb_build_array(
            jsonb_build_object(
                'label', 'regular',
                'pricing', le.pricing_override,
                'valid_from', NULL,
                'valid_until', NULL,
                'sort_order', 0
            )
        )
        WHERE le.pricing_tiers IS NULL
          AND le.pricing_override IS NOT NULL
          AND jsonb_typeof(le.pricing_override) = 'array'
        """
    )


def downgrade() -> None:
    """Drop the ``pricing_tiers`` column. Data in it is lost on rollback."""
    op.execute("ALTER TABLE launch_editions DROP COLUMN IF EXISTS pricing_tiers")
