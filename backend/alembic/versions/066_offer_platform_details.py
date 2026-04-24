"""offer: +platform_details composable JSONB column (Fase 02 · Block G)

Revision ID: 066_offer_platform_details
Revises: 065_offer_subscription_details_rename
Create Date: 2026-04-24

Adds `products.platform_details` as a composable JSONB column (NULL by
default). Lives separately from `specific_details` — the 14 SaaS-flavored
fields are orthogonal to ``OfferArchetype`` (any offer can be SaaS-flavored
regardless of being MEMBRESIA or not). See ADR-010.

refs: docs/refactors/field-contract-ssot/phases/02-migrate-sections/
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "066_offer_platform_details"
down_revision: str | None = "065_offer_subscription_details_rename"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add composable platform_details JSONB column (idempotent)."""
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS platform_details JSONB")


def downgrade() -> None:
    """Explicit NO-OP. Composable column is purely additive."""
