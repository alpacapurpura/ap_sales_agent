"""Create brand_extraction_traces table for extraction performance tracing.

Revision ID: 014_brand_extraction_traces
Revises: 013_create_avatars_assets
Create Date: 2026-03-23
"""
from alembic import op

# revision identifiers
revision = "014_brand_extraction_traces"
down_revision = "013_create_avatars_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS brand_extraction_traces (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            job_id VARCHAR NOT NULL,
            mode VARCHAR NOT NULL,
            profile_name VARCHAR NOT NULL,
            url TEXT,
            include_visuals VARCHAR DEFAULT 'false',
            include_assets VARCHAR DEFAULT 'false',
            status VARCHAR NOT NULL DEFAULT 'running',
            content_length INTEGER DEFAULT 0,
            sections_total INTEGER DEFAULT 0,
            sections_succeeded INTEGER DEFAULT 0,
            total_duration_s FLOAT,
            error_message TEXT,
            events JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_brand_extraction_traces_tenant_id ON brand_extraction_traces (tenant_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_brand_extraction_traces_job_id ON brand_extraction_traces (job_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_brand_extraction_traces_created_at ON brand_extraction_traces (created_at DESC);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS brand_extraction_traces;")
