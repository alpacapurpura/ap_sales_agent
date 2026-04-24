"""offer: +value-stack anchor columns (Fase 02 · Block B)

Revision ID: 064_offer_value_stack_anchor
Revises: 063_offer_authority_block
Create Date: 2026-04-24

Columns added to `products` (idempotent):
  - total_perceived_value_anchor (NUMERIC(12,2), NULL): USD anchor number
    shown on landing + sales-agent ("Valor total USD 4344 · Tu inversión
    USD 1497"). Sin esto el stack pierde 40-60% de impacto.
  - stack_positioning_statement (TEXT, NULL): 2-3 line statement that
    captures the trade-off "valor vs precio" — reused en landing + cierre
    del agente.

refs: docs/refactors/field-contract-ssot/phases/02-migrate-sections/
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "064_offer_value_stack_anchor"
down_revision: str | None = "063_offer_authority_block"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add value-stack anchor columns (idempotent)."""
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS total_perceived_value_anchor NUMERIC(12, 2)")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS stack_positioning_statement TEXT")


def downgrade() -> None:
    """Explicit NO-OP. Value-stack anchor columns are purely additive."""
