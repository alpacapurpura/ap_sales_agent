"""Assets: scope, purpose, extraction columns + asset_links table.

Introduces the three orthogonal axes for asset lifecycle:

1. ``scope``   — ephemeral | library | deliverable
2. ``purpose`` — context_extract | visual_reference | brand_asset |
                 offer_collateral | legal_doc | testimonial | knowledge_source
3. ``asset_links`` — polymorphic connection between an asset and any
                    domain entity (offer/brand/flow_phase/...) with a role.

Also adds text-extraction columns so document content is processed once
at upload and re-used across conversations instead of being re-parsed on
every LLM turn.

Existing rows are back-filled as ``library`` / ``brand_asset`` to avoid
their surprise expiry — they predate the copilot chat upload flow.

Revision ID: 057_asset_scope_purpose
Revises: 056_copilot_multimodal
Create Date: 2026-04-22 14:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "057_asset_scope_purpose"
down_revision: str | None = "056_copilot_multimodal"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Idempotent raw SQL — follows .claude/rules/backend-migrations.md."""
    # ── assets: new columns ──────────────────────────────────────────────
    op.execute(
        """
        ALTER TABLE assets
          ADD COLUMN IF NOT EXISTS scope VARCHAR(20),
          ADD COLUMN IF NOT EXISTS purpose VARCHAR(40),
          ADD COLUMN IF NOT EXISTS extracted_text TEXT,
          ADD COLUMN IF NOT EXISTS extracted_summary VARCHAR(500),
          ADD COLUMN IF NOT EXISTS extracted_at TIMESTAMPTZ,
          ADD COLUMN IF NOT EXISTS extraction_status VARCHAR(20),
          ADD COLUMN IF NOT EXISTS extraction_error TEXT,
          ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ
        """
    )

    # ── Back-fill legacy rows to library/brand_asset ─────────────────────
    # Historical uploads predate the copilot chat flow — they live in offer
    # galleries and brand assets. Treating them as ephemeral would schedule
    # them for purge; library + brand_asset preserves existing behavior.
    op.execute(
        """
        UPDATE assets SET scope = 'library' WHERE scope IS NULL;
        UPDATE assets SET purpose = 'brand_asset' WHERE purpose IS NULL;
        UPDATE assets SET extraction_status = 'pending' WHERE extraction_status IS NULL;
        """
    )

    # Lock defaults + NOT NULL once back-fill ran.
    op.execute(
        """
        ALTER TABLE assets
          ALTER COLUMN scope SET DEFAULT 'ephemeral',
          ALTER COLUMN scope SET NOT NULL,
          ALTER COLUMN purpose SET DEFAULT 'context_extract',
          ALTER COLUMN purpose SET NOT NULL,
          ALTER COLUMN extraction_status SET DEFAULT 'pending',
          ALTER COLUMN extraction_status SET NOT NULL
        """
    )

    # Indexes for the query shapes we actually use:
    #  - search_assets filters by (tenant_id, scope, deleted_at IS NULL).
    #  - purge worker scans (scope='ephemeral', expires_at <= now()).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_assets_tenant_scope
          ON assets (tenant_id, scope)
          WHERE deleted_at IS NULL;

        CREATE INDEX IF NOT EXISTS ix_assets_ephemeral_expires
          ON assets (expires_at)
          WHERE scope = 'ephemeral' AND deleted_at IS NULL;
        """
    )

    # ── asset_links: polymorphic asset → entity mapping ──────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS asset_links (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          tenant_id UUID NOT NULL,
          asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
          entity_type VARCHAR(40) NOT NULL,
          entity_id UUID NOT NULL,
          role VARCHAR(40) NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          deleted_at TIMESTAMPTZ
        )
        """
    )

    # Unique constraint: same (asset, entity, role) cannot be linked twice
    # simultaneously. Soft-deleted rows are excluded so re-promoting works.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_asset_links_unique_active
          ON asset_links (tenant_id, asset_id, entity_type, entity_id, role)
          WHERE deleted_at IS NULL
        """
    )

    # Query indexes: sales_agent looks up by (entity_type, entity_id, role);
    # UI looks up by (asset_id).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_asset_links_entity
          ON asset_links (tenant_id, entity_type, entity_id, role)
          WHERE deleted_at IS NULL;

        CREATE INDEX IF NOT EXISTS ix_asset_links_asset
          ON asset_links (asset_id)
          WHERE deleted_at IS NULL;
        """
    )


def downgrade() -> None:
    """Reverse the upgrade — drops columns, indexes, and the link table."""
    op.execute("DROP TABLE IF EXISTS asset_links CASCADE")
    op.execute(
        """
        DROP INDEX IF EXISTS ix_assets_tenant_scope;
        DROP INDEX IF EXISTS ix_assets_ephemeral_expires;
        ALTER TABLE assets
          DROP COLUMN IF EXISTS scope,
          DROP COLUMN IF EXISTS purpose,
          DROP COLUMN IF EXISTS extracted_text,
          DROP COLUMN IF EXISTS extracted_summary,
          DROP COLUMN IF EXISTS extracted_at,
          DROP COLUMN IF EXISTS extraction_status,
          DROP COLUMN IF EXISTS extraction_error,
          DROP COLUMN IF EXISTS expires_at
        """
    )
