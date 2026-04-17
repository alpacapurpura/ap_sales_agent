"""create enrollments table (Phase 5)

Persists leads inscribed in offer editions with payment tracking. Backs
the sales-agent enrollment tools (Phase 6), the Closer Studio global
``/sales/enrollments`` page (Phase 9c), and the per-edition Ventas tab
(Phase 9b).

Idempotency: every ``CREATE`` uses ``IF NOT EXISTS`` so partial reruns
are safe. ``enrollments.edition_id`` is nullable because leads inscribed
into a waitlist exist before an edition has been committed.

Revision ID: 048_create_enrollments
Revises: 047_pricing_tiers
Create Date: 2026-04-17 02:30:00.000000
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "048_create_enrollments"
down_revision: str | None = "047_pricing_tiers"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the enrollments table + supporting indexes."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS enrollments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            offer_id UUID NOT NULL REFERENCES products(id),
            edition_id UUID NULL REFERENCES launch_editions(id) ON DELETE SET NULL,
            contact_id UUID NOT NULL,
            conversation_id UUID NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'intent',
            pricing_tier_label VARCHAR(64) NULL,
            pricing_amount DOUBLE PRECISION NULL,
            currency VARCHAR(8) NULL,
            payment_provider VARCHAR(32) NULL,
            payment_transaction_id VARCHAR(256) NULL,
            payment_link_url TEXT NULL,
            paid_at TIMESTAMPTZ NULL,
            source_channel VARCHAR(64) NULL,
            notes TEXT NULL,
            extra JSONB NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NULL
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_tenant ON enrollments (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_offer ON enrollments (tenant_id, offer_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_edition ON enrollments (tenant_id, edition_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_contact ON enrollments (tenant_id, contact_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_status ON enrollments (tenant_id, status)")
    # Partial index for waitlist listings — keeps scan cheap when promoting.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_enrollments_waitlist
        ON enrollments (tenant_id, offer_id)
        WHERE status = 'waitlist'
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_conversation ON enrollments (conversation_id)")


def downgrade() -> None:
    """Drop table and indexes."""
    op.execute("DROP TABLE IF EXISTS enrollments")
