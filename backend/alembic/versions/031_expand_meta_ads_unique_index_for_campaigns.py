"""expand_meta_ads_unique_index_for_campaigns

Add campaign_id, ad_set_id, ad_id to the unique constraint on
official_metrics and staging_metrics so campaign-level rows don't
conflict with account-level rows.

Revision ID: 031_expand_meta_ads_campaign_idx
Revises: 030_add_lead_id_to_appointments
Create Date: 2026-04-02
"""
from alembic import op

revision = "031_expand_meta_ads_campaign_idx"
down_revision = "030_add_lead_id_to_appointments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add campaign dimension columns if they don't exist
    for table in ("official_metrics", "staging_metrics"):
        for col in ("campaign_id", "ad_set_id", "ad_id"):
            op.execute(f"""
                ALTER TABLE {table}
                ADD COLUMN IF NOT EXISTS {col} VARCHAR(255) DEFAULT NULL
            """)

    # Drop old unique indexes
    op.execute("DROP INDEX IF EXISTS uq_official_metrics_natural_key")
    op.execute("DROP INDEX IF EXISTS uq_staging_metrics_natural_key")

    # Create expanded unique indexes with COALESCE for NULL campaign dimensions
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_official_metrics_natural_key
        ON official_metrics (
            tenant_id, provider, channel_slug, metric_name, metric_date,
            COALESCE(campaign_id, ''), COALESCE(ad_set_id, ''), COALESCE(ad_id, '')
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_staging_metrics_natural_key
        ON staging_metrics (
            tenant_id, provider, channel_slug, metric_name, metric_date,
            COALESCE(campaign_id, ''), COALESCE(ad_set_id, ''), COALESCE(ad_id, '')
        )
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_official_metrics_natural_key")
    op.execute("DROP INDEX IF EXISTS uq_staging_metrics_natural_key")
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_official_metrics_natural_key
        ON official_metrics (tenant_id, provider, channel_slug, metric_name, metric_date)
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_staging_metrics_natural_key
        ON staging_metrics (tenant_id, provider, channel_slug, metric_name, metric_date)
    """)
