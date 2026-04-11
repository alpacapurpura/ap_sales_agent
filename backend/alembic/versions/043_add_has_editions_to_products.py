"""add has_editions column to products

Revision ID: 043_add_has_editions
Revises: 042_offer_header_refactor
Create Date: 2026-04-11 12:00:00.000000

Wizard-driven flag capturing the user's intent: does this offer run in
editions/cohorts/batches? Drives visibility of the 'Ediciones' section in
the offer editor.

Backfill is archetype-aware so existing offers keep their current UX:
- PROGRAMA / SERVICIO / EXPERIENCIA  → TRUE  (section stays visible)
- PRODUCTO / MEMBRESIA               → FALSE (section never applied)

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "043_add_has_editions"
down_revision: str | None = "042_offer_header_refactor"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add column with a safe default (TRUE) so new inserts work before the
    # application layer is aware of the field.
    op.execute("""
        ALTER TABLE products
        ADD COLUMN IF NOT EXISTS has_editions BOOLEAN NOT NULL DEFAULT TRUE
    """)

    # Backfill: PRODUCTO and MEMBRESIA never have editions.
    # Archetype values are stored lowercase in the string column.
    op.execute("""
        UPDATE products
        SET has_editions = FALSE
        WHERE archetype IN ('producto', 'membresia')
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS has_editions")
