"""add preset_id to products (Sprint 14)

Introduces the link from each ``Offer`` (stored in legacy ``products``
table) to its ``OfferTypePreset`` — the 7th SSoT axis registered in
``src/modules/offer/domain/offer_type_preset_catalog.py``.

The column is nullable because:
- Pre-Sprint-12 offers have no preset concept (legacy data is valid).
- The wizard rehaul that always asks for a preset ships in Sprint 13
  — until then, some newly created offers may legitimately lack one.
- A separate backfill script
  (``backend/scripts/backfill_offer_preset_id.py``) populates existing
  rows by matching the tenant's first declared ``business_type`` +
  the offer's ``archetype`` against the catalog's default pairs.

Idempotency:
    ``ADD COLUMN IF NOT EXISTS`` and ``CREATE INDEX IF NOT EXISTS`` make
    reruns safe. The backfill is orthogonal (lives in a script) — this
    migration only owns schema evolution.

Index rationale:
    Analytics and the sales-agent grounding query by
    ``(tenant_id, preset_id)`` to filter offers by preset family. GIN
    / GiST are overkill for equality — a btree composite index is the
    right tool.

Revision ID: 050_add_offer_preset_id
Revises: 049_variant_structure
Create Date: 2026-04-19 12:00:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "050_add_offer_preset_id"
down_revision: str | None = "049_variant_structure"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add ``preset_id`` column + supporting composite index."""
    op.execute(
        """
        ALTER TABLE products
            ADD COLUMN IF NOT EXISTS preset_id TEXT
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_products_tenant_preset
            ON products (tenant_id, preset_id)
            WHERE preset_id IS NOT NULL
        """
    )


def downgrade() -> None:
    """Reverse: drop index, then column."""
    op.execute("DROP INDEX IF EXISTS ix_products_tenant_preset")
    op.execute(
        """
        ALTER TABLE products
            DROP COLUMN IF EXISTS preset_id
        """
    )
