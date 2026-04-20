"""add variant_structure, structure_data, sort_rank to launch_editions (Sprint 7)

Introduces the sixth SSoT axis — ``VariantStructure`` — at the storage
layer. Every ``LaunchEdition`` is now tagged with the structure it
instances, carries arbitrary structure-specific metadata in a
``structure_data`` JSONB blob, and exposes an optional ``sort_rank`` for
orderable structures (TIER / SKU_VARIANT / REGIONAL / MODALITY / LANGUAGE).

Backfill strategy:
    Existing rows are mapped deterministically from the parent offer's
    archetype via the Sprint-8 migration mapping. This is intentionally
    redundant with the archetype catalog — hard-coding here keeps the
    migration reproducible against older code versions.

    - PROGRAMA → temporal_cohort
    - EXPERIENCIA → temporal_single_date
    - SERVICIO → recurring_intake
    - PRODUCTO / MEMBRESIA → no rows exist pre-Sprint-7 (supports_editions=False)

Idempotency:
    Every ``ALTER`` uses ``IF NOT EXISTS`` so partial reruns are safe.
    Backfill is an ``UPDATE ... WHERE variant_structure IS NULL`` so
    re-running never overrides curated data. The ``SET NOT NULL`` step
    short-circuits if the column is already NOT NULL.

Indexes:
    - Composite btree on ``(offer_id, variant_structure)`` — supports
      per-offer variant filtering ("give me all TIER rows for this offer").
    - GIN on ``structure_data jsonb_path_ops`` — supports ``@>`` queries
      on SKU attributes, regional country codes, etc. Uses
      ``jsonb_path_ops`` (not default ``jsonb_ops``) because the query
      pattern is always containment, not arbitrary path search — smaller
      index + faster containment.

Revision ID: 049_variant_structure
Revises: 048_create_enrollments
Create Date: 2026-04-18 12:00:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "049_variant_structure"
down_revision: str | None = "048_create_enrollments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add variant_structure axis columns + backfill from archetype."""
    # --- Add columns (nullable first so backfill can populate) --------------
    op.execute(
        """
        ALTER TABLE launch_editions
            ADD COLUMN IF NOT EXISTS variant_structure TEXT,
            ADD COLUMN IF NOT EXISTS structure_data JSONB NOT NULL DEFAULT '{}'::jsonb,
            ADD COLUMN IF NOT EXISTS sort_rank INTEGER
        """
    )

    # --- Backfill variant_structure from parent offer's archetype -----------
    # Mapping mirrors Sprint-8 ``ArchetypeCapabilities.default_variant_structure``.
    # Hard-coded here so the migration is reproducible even if the catalog is
    # edited later. The WHERE clause guards against overwriting curated data on
    # partial reruns.
    op.execute(
        """
        UPDATE launch_editions le
        SET variant_structure = CASE p.archetype
            WHEN 'programa'    THEN 'temporal_cohort'
            WHEN 'experiencia' THEN 'temporal_single_date'
            WHEN 'servicio'    THEN 'recurring_intake'
            ELSE 'temporal_cohort'
        END
        FROM products p
        WHERE le.offer_id = p.id
          AND le.variant_structure IS NULL
        """
    )

    # --- Enforce NOT NULL now that every row has a value --------------------
    # Conditional on the column not already being NOT NULL — re-runs are
    # no-ops and do not error.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'launch_editions'
                  AND column_name = 'variant_structure'
                  AND is_nullable = 'YES'
            ) THEN
                ALTER TABLE launch_editions
                    ALTER COLUMN variant_structure SET NOT NULL;
            END IF;
        END
        $$
        """
    )

    # --- Supporting indexes -------------------------------------------------
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_launch_editions_offer_structure
            ON launch_editions (offer_id, variant_structure)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_launch_editions_structure_data_gin
            ON launch_editions USING gin (structure_data jsonb_path_ops)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_launch_editions_sort_rank
            ON launch_editions (offer_id, variant_structure, sort_rank)
            WHERE sort_rank IS NOT NULL
        """
    )


def downgrade() -> None:
    """Reverse the schema change — drop indexes then columns."""
    op.execute("DROP INDEX IF EXISTS ix_launch_editions_sort_rank")
    op.execute("DROP INDEX IF EXISTS ix_launch_editions_structure_data_gin")
    op.execute("DROP INDEX IF EXISTS ix_launch_editions_offer_structure")
    op.execute(
        """
        ALTER TABLE launch_editions
            DROP COLUMN IF EXISTS sort_rank,
            DROP COLUMN IF EXISTS structure_data,
            DROP COLUMN IF EXISTS variant_structure
        """
    )
