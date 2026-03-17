"""add_etl_infrastructure_tables_and_tenant_priority

Revision ID: ab8346fd2c09
Revises: f5a6b7c8d9e0
Create Date: 2026-03-15 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ab8346fd2c09"
down_revision: Union[str, None] = "f5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- extraction_runs ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS extraction_runs (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            provider VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'pending',
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            error TEXT,
            metrics_count INTEGER DEFAULT 0,
            duration_seconds FLOAT,
            rows_extracted INTEGER DEFAULT 0,
            rate_limit_headroom FLOAT,
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_extraction_runs_tenant_id ON extraction_runs (tenant_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_extraction_tenant_provider_status ON extraction_runs (tenant_id, provider, status);")

    # --- staging_metrics ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS staging_metrics (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            provider VARCHAR NOT NULL,
            channel_slug VARCHAR NOT NULL,
            metric_name VARCHAR NOT NULL,
            value FLOAT NOT NULL,
            unit VARCHAR NOT NULL,
            currency VARCHAR,
            metric_date DATE NOT NULL,
            spend JSONB,
            revenue JSONB,
            campaign_id VARCHAR,
            ad_set_id VARCHAR,
            ad_id VARCHAR,
            extra JSONB DEFAULT '{}',
            extraction_run_id UUID REFERENCES extraction_runs(id),
            created_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_staging_metrics_tenant_id ON staging_metrics (tenant_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_staging_metrics_provider ON staging_metrics (provider);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_staging_metrics_metric_date ON staging_metrics (metric_date);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_staging_tenant_provider_date ON staging_metrics (tenant_id, provider, metric_date);")

    # --- official_metrics ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS official_metrics (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            provider VARCHAR NOT NULL,
            channel_slug VARCHAR NOT NULL,
            metric_name VARCHAR NOT NULL,
            value FLOAT NOT NULL,
            unit VARCHAR NOT NULL,
            currency VARCHAR,
            metric_date DATE NOT NULL,
            spend JSONB,
            revenue JSONB,
            campaign_id VARCHAR,
            ad_set_id VARCHAR,
            ad_id VARCHAR,
            cost_type VARCHAR,
            extra JSONB DEFAULT '{}',
            source_extraction_run_id UUID,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_official_metrics_tenant_id ON official_metrics (tenant_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_official_metrics_metric_date ON official_metrics (metric_date);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_official_tenant_channel_date ON official_metrics (tenant_id, channel_slug, metric_date);")

    # --- metric_aggregations ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS metric_aggregations (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            channel_slug VARCHAR NOT NULL,
            metric_name VARCHAR NOT NULL,
            period_type VARCHAR NOT NULL,
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            value FLOAT NOT NULL,
            unit VARCHAR NOT NULL,
            currency VARCHAR,
            cost_type VARCHAR,
            computed_at TIMESTAMPTZ DEFAULT now(),
            extraction_run_id UUID
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_metric_aggregations_tenant_id ON metric_aggregations (tenant_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_agg_tenant_channel_period ON metric_aggregations (tenant_id, channel_slug, period_type, period_start);")

    # --- Add extraction_priority to tenants ---
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS extraction_priority INTEGER NOT NULL DEFAULT 0;")


def downgrade() -> None:
    op.drop_column("tenants", "extraction_priority")
    op.drop_table("metric_aggregations")
    op.drop_table("official_metrics")
    op.drop_table("staging_metrics")
    op.drop_table("extraction_runs")
