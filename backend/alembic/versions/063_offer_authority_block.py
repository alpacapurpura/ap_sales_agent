"""offer: +authority narrative columns (Fase 02 · Block A)

Revision ID: 063_offer_authority_block
Revises: 062_offer_pricing_latam
Create Date: 2026-04-24

Columns added to `products` (idempotent):
  - authority_positioning_for_sales (TEXT, NULL): sales-agent-friendly
    narrative positioning of the instructor. Replaces ad-hoc text stitched
    in prompts.
  - authority_notes (TEXT, NULL): per-offer credential notes that override
    the brand-studio KeyFigure bio without mutating the master profile.

refs: docs/refactors/field-contract-ssot/phases/02-migrate-sections/
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "063_offer_authority_block"
down_revision: str | None = "062_offer_pricing_latam"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add 2 authority narrative columns (idempotent)."""
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS authority_positioning_for_sales TEXT")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS authority_notes TEXT")


def downgrade() -> None:
    """Explicit NO-OP. Authority columns are purely additive."""
