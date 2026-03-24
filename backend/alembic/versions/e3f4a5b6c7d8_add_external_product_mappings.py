"""add external_product_mappings table

Revision ID: e3f4a5b6c7d8
Revises: 014_brand_extraction_traces
Create Date: 2026-03-24

"""
from alembic import op

revision = "e3f4a5b6c7d8"
down_revision = "014_brand_extraction_traces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS external_product_mappings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            offer_id UUID NOT NULL REFERENCES products(id),
            source VARCHAR NOT NULL,
            external_id VARCHAR NOT NULL,
            external_name VARCHAR,
            external_variant_id VARCHAR,
            metadata_info JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        );
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_external_product_mapping_tenant_source_ext
        ON external_product_mappings (tenant_id, source, external_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_external_product_mappings_tenant_id
        ON external_product_mappings (tenant_id);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS external_product_mappings;")
