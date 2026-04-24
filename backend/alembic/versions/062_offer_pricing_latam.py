"""offer: +3 pricing LATAM columns

Revision ID: 062_offer_pricing_latam
Revises: 061_offer_narrative_fields
Create Date: 2026-04-24

Columns added to `products`:
  pricing:    tax_included (bool), installments_available (text),
              accepted_payment_providers (jsonb[])

refs: docs/refactors/field-contract-ssot/phases/01-field-contract-pilot-pricing/
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "062_offer_pricing_latam"
down_revision: str | None = "061_offer_narrative_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add 3 pricing LATAM columns to products table (idempotent)."""
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS tax_included BOOLEAN")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS installments_available TEXT")
    op.execute(
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS accepted_payment_providers JSONB NOT NULL DEFAULT '[]'::jsonb"
    )


def downgrade() -> None:
    """Explicit NO-OP.

    Pricing LATAM columns are purely additive; dropping them would destroy
    tenant data. Use a forward-only migration if a rollback is really needed.
    """
