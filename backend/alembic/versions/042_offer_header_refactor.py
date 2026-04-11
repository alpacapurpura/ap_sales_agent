"""offer header refactor: assets, knowledge sources, lifecycle, landing snapshots

Revision ID: 042_offer_header_refactor
Revises: 041_add_external_id_to_messages
Create Date: 2026-04-11

Adds:
  * `offer_assets` — flyer / video / carousel / document per offer.
  * `offer_knowledge_sources` — PDFs / videos / URLs for Sales Agent RAG.
  * `products.paused_at`, `products.status_changed_at`,
    `products.completion_percentage` — lifecycle + completion %.
  * `products_status_check` — CHECK constraint including the new
    `paused` status.
  * `landing_pages.generated_at`, `.offer_snapshot_version`,
    `.generation_job_id`, `.generation_job_status`, `.generation_error` —
    generation snapshot / job tracking.

Idempotent raw SQL only (per `.claude/rules/backend-migrations.md`). Safe to
re-run.
"""

from alembic import op

revision = "042_offer_header_refactor"
down_revision = "041_add_external_id_to_messages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- offer_assets -------------------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_assets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            offer_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            name VARCHAR NOT NULL,
            type VARCHAR NOT NULL,
            source VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'draft',
            file_url VARCHAR,
            thumbnail_url VARCHAR,
            mime_type VARCHAR,
            size_bytes INTEGER,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            prompt_params JSONB,
            editable_in_puck BOOLEAN NOT NULL DEFAULT false,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offer_assets_tenant_id "
        "ON offer_assets (tenant_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offer_assets_offer_id "
        "ON offer_assets (offer_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offer_assets_tenant_offer "
        "ON offer_assets (tenant_id, offer_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offer_assets_deleted_at "
        "ON offer_assets (deleted_at);"
    )

    # CHECK: writable subset of asset type / source / status enums.
    op.execute(
        """
        ALTER TABLE offer_assets DROP CONSTRAINT IF EXISTS offer_assets_type_check;
        ALTER TABLE offer_assets ADD CONSTRAINT offer_assets_type_check
            CHECK (type IN ('flyer','video','carousel','document','image'));
        """
    )
    op.execute(
        """
        ALTER TABLE offer_assets DROP CONSTRAINT IF EXISTS offer_assets_source_check;
        ALTER TABLE offer_assets ADD CONSTRAINT offer_assets_source_check
            CHECK (source IN ('ai','external'));
        """
    )
    op.execute(
        """
        ALTER TABLE offer_assets DROP CONSTRAINT IF EXISTS offer_assets_status_check;
        ALTER TABLE offer_assets ADD CONSTRAINT offer_assets_status_check
            CHECK (status IN ('draft','processing','ready','error'));
        """
    )

    # --- offer_knowledge_sources --------------------------------------------
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_knowledge_sources (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            offer_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            name VARCHAR NOT NULL,
            type VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'queued',
            source_url VARCHAR,
            file_url VARCHAR,
            mime_type VARCHAR,
            size_bytes INTEGER,
            indexed_chunk_count INTEGER NOT NULL DEFAULT 0,
            last_indexed_at TIMESTAMPTZ,
            qdrant_collection VARCHAR,
            qdrant_point_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ
        );
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offer_knowledge_sources_tenant_id "
        "ON offer_knowledge_sources (tenant_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offer_knowledge_sources_offer_id "
        "ON offer_knowledge_sources (offer_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offer_knowledge_sources_tenant_offer "
        "ON offer_knowledge_sources (tenant_id, offer_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offer_knowledge_sources_deleted_at "
        "ON offer_knowledge_sources (deleted_at);"
    )

    op.execute(
        """
        ALTER TABLE offer_knowledge_sources
            DROP CONSTRAINT IF EXISTS offer_knowledge_sources_type_check;
        ALTER TABLE offer_knowledge_sources
            ADD CONSTRAINT offer_knowledge_sources_type_check
            CHECK (type IN (
                'pdf','docx','txt','markdown','video',
                'url_youtube','url_article','url_google_doc'
            ));
        """
    )
    op.execute(
        """
        ALTER TABLE offer_knowledge_sources
            DROP CONSTRAINT IF EXISTS offer_knowledge_sources_status_check;
        ALTER TABLE offer_knowledge_sources
            ADD CONSTRAINT offer_knowledge_sources_status_check
            CHECK (status IN ('queued','processing','indexed','error'));
        """
    )

    # --- products: lifecycle + completion -----------------------------------
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS paused_at TIMESTAMPTZ;")
    op.execute(
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS status_changed_at TIMESTAMPTZ;"
    )
    op.execute(
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS completion_percentage FLOAT;"
    )
    # Refresh the status CHECK so 'paused' is valid alongside the existing
    # values. We drop+recreate unconditionally (idempotent).
    op.execute(
        """
        ALTER TABLE products DROP CONSTRAINT IF EXISTS products_status_check;
        ALTER TABLE products ADD CONSTRAINT products_status_check
            CHECK (status IN (
                'draft','active','paused','archived','waitlist','sold_out'
            ));
        """
    )

    # --- landing_pages: generation snapshot ---------------------------------
    op.execute(
        """
        ALTER TABLE landing_pages
            ADD COLUMN IF NOT EXISTS generated_at TIMESTAMPTZ;
        """
    )
    op.execute(
        """
        ALTER TABLE landing_pages
            ADD COLUMN IF NOT EXISTS offer_snapshot_version VARCHAR;
        """
    )
    op.execute(
        """
        ALTER TABLE landing_pages
            ADD COLUMN IF NOT EXISTS generation_job_id UUID;
        """
    )
    op.execute(
        """
        ALTER TABLE landing_pages
            ADD COLUMN IF NOT EXISTS generation_job_status VARCHAR;
        """
    )
    op.execute(
        """
        ALTER TABLE landing_pages
            ADD COLUMN IF NOT EXISTS generation_error TEXT;
        """
    )


def downgrade() -> None:
    # Reference-only downgrade (not required to work per project rules).
    # We leave the new tables and columns in place; a dedicated rollback
    # migration can be added if ever needed.
    pass
