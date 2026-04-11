"""add archived_at and deleted_at to products (offers)

Revision ID: 040_add_archived_deleted_products
Revises: 039_add_ad_offer_assoc
Create Date: 2026-04-11 00:00:00.000000

Introduces two lifecycle columns on the `products` table so offers
(including lead magnets) can be archived (reversible) and soft-deleted
(hidden everywhere, for future "delete" action from archived view).

- `archived_at` NULL  + `deleted_at` NULL  -> Active
- `archived_at` NOT   NULL + `deleted_at` NULL -> Archived (visible in /archived)
- `deleted_at` NOT NULL                   -> Soft-deleted (hidden always)

Backfill: rows currently using `status='archived'` as a soft-archive
mechanism are migrated to the new model. Their status is reset to 'draft'
so the operational `status` column is left free for its real meaning
(draft/active/paused/waitlist/sold_out).

Partial indexes optimise the two hot queries: list_active and list_archived.
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "040_add_archived_deleted_products"
down_revision: str | None = "039_add_ad_offer_assoc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Columns (idempotent)
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS deleted_at  TIMESTAMPTZ")

    # Partial indexes for active and archived listings
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_products_active_by_tenant
        ON products (tenant_id)
        WHERE archived_at IS NULL AND deleted_at IS NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_products_archived_by_tenant
        ON products (tenant_id, archived_at DESC)
        WHERE archived_at IS NOT NULL AND deleted_at IS NULL
        """
    )

    # Backfill: move legacy status='archived' rows to the new lifecycle column
    # and reset their status to draft so the operational status stays clean.
    op.execute(
        """
        UPDATE products
           SET archived_at = COALESCE(updated_at, created_at, NOW()),
               status = 'draft'
         WHERE status = 'archived'
           AND archived_at IS NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_products_archived_by_tenant")
    op.execute("DROP INDEX IF EXISTS ix_products_active_by_tenant")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS deleted_at")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS archived_at")
