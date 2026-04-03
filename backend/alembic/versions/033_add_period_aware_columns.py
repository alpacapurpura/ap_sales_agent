"""add_period_aware_columns

Adds period configuration to tenants, period key columns to official_metrics,
creates period_metrics table, adds extraction_type to extraction_runs,
and unique index on metric_aggregations.

Revision ID: 033_add_period_aware_columns
Revises: 032_campaign_management
Create Date: 2026-04-03
"""
from alembic import op

revision = "033_add_period_aware_columns"
down_revision = "032_campaign_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Tenant period config ──
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS weekly_start_day INTEGER DEFAULT 0"
    )
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS fiscal_year_start_month INTEGER DEFAULT 1"
    )
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS fiscal_year_start_day INTEGER DEFAULT 1"
    )

    # ── Period key columns on official_metrics ──
    op.execute(
        "ALTER TABLE official_metrics ADD COLUMN IF NOT EXISTS iso_week_start DATE"
    )
    op.execute(
        "ALTER TABLE official_metrics ADD COLUMN IF NOT EXISTS month_key VARCHAR(7)"
    )
    op.execute(
        "ALTER TABLE official_metrics ADD COLUMN IF NOT EXISTS quarter_key VARCHAR(7)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_official_week "
        "ON official_metrics (tenant_id, iso_week_start)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_official_month "
        "ON official_metrics (tenant_id, month_key)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_official_quarter "
        "ON official_metrics (tenant_id, quarter_key)"
    )

    # ── Backfill existing rows ──
    op.execute("""
        UPDATE official_metrics SET
            iso_week_start = metric_date - (EXTRACT(ISODOW FROM metric_date)::int - 1) * INTERVAL '1 day',
            month_key = TO_CHAR(metric_date, 'YYYY-MM'),
            quarter_key = TO_CHAR(metric_date, 'YYYY') || '-Q' || EXTRACT(QUARTER FROM metric_date)::int
        WHERE iso_week_start IS NULL
    """)

    # ── Extraction runs: period columns ──
    op.execute(
        "ALTER TABLE extraction_runs ADD COLUMN IF NOT EXISTS "
        "extraction_type VARCHAR DEFAULT 'daily'"
    )
    op.execute(
        "ALTER TABLE extraction_runs ADD COLUMN IF NOT EXISTS period_start DATE"
    )
    op.execute(
        "ALTER TABLE extraction_runs ADD COLUMN IF NOT EXISTS period_end DATE"
    )

    # ── period_metrics table ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS period_metrics (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            provider VARCHAR NOT NULL,
            channel_slug VARCHAR NOT NULL,
            metric_name VARCHAR NOT NULL,
            value FLOAT NOT NULL,
            unit VARCHAR NOT NULL,
            currency VARCHAR,
            period_type VARCHAR NOT NULL,
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            campaign_id VARCHAR,
            ad_set_id VARCHAR,
            ad_id VARCHAR,
            cost_type VARCHAR,
            extra JSONB DEFAULT '{}',
            source_extraction_run_id UUID,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        )
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_period_metrics_natural_key
        ON period_metrics (
            tenant_id, provider, channel_slug, metric_name,
            period_type, period_start,
            COALESCE(campaign_id, ''), COALESCE(ad_set_id, ''), COALESCE(ad_id, '')
        )
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_period_metrics_tenant_period
        ON period_metrics (tenant_id, channel_slug, period_type, period_start)
    """)

    # ── Unique index on metric_aggregations ──
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_metric_agg_natural_key
        ON metric_aggregations (
            tenant_id, channel_slug, metric_name, period_type, period_start
        )
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_metric_agg_natural_key")
    op.execute("DROP INDEX IF EXISTS ix_period_metrics_tenant_period")
    op.execute("DROP INDEX IF EXISTS uq_period_metrics_natural_key")
    op.execute("DROP TABLE IF EXISTS period_metrics")
    op.execute("ALTER TABLE extraction_runs DROP COLUMN IF EXISTS extraction_type")
    op.execute("ALTER TABLE extraction_runs DROP COLUMN IF EXISTS period_start")
    op.execute("ALTER TABLE extraction_runs DROP COLUMN IF EXISTS period_end")
    op.execute("DROP INDEX IF EXISTS ix_official_quarter")
    op.execute("DROP INDEX IF EXISTS ix_official_month")
    op.execute("DROP INDEX IF EXISTS ix_official_week")
    op.execute("ALTER TABLE official_metrics DROP COLUMN IF EXISTS quarter_key")
    op.execute("ALTER TABLE official_metrics DROP COLUMN IF EXISTS month_key")
    op.execute("ALTER TABLE official_metrics DROP COLUMN IF EXISTS iso_week_start")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS fiscal_year_start_day")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS fiscal_year_start_month")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS weekly_start_day")
