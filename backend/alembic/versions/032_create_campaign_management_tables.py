"""create_campaign_management_tables

Tables for storing Meta campaign hierarchy metadata and recommendations.

Revision ID: 032_campaign_management
Revises: 031_expand_meta_ads_campaign_idx
Create Date: 2026-04-02
"""
from alembic import op

revision = "032_campaign_management"
down_revision = "031_expand_meta_ads_campaign_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── ad_campaigns ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS ad_campaigns (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            provider VARCHAR(50) NOT NULL DEFAULT 'meta',
            external_id VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            objective VARCHAR(100),
            status VARCHAR(50),
            effective_status VARCHAR(50),
            bid_strategy VARCHAR(100),
            daily_budget BIGINT,
            lifetime_budget BIGINT,
            budget_remaining BIGINT,
            buying_type VARCHAR(50) DEFAULT 'AUCTION',
            special_ad_categories JSONB DEFAULT '[]'::jsonb,
            start_time TIMESTAMPTZ,
            stop_time TIMESTAMPTZ,
            external_created_time TIMESTAMPTZ,
            external_updated_time TIMESTAMPTZ,
            extra JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ad_campaigns_tenant_provider_ext
        ON ad_campaigns (tenant_id, provider, external_id)
        WHERE deleted_at IS NULL
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_ad_campaigns_tenant ON ad_campaigns (tenant_id)")

    # ── ad_sets ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS ad_sets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            provider VARCHAR(50) NOT NULL DEFAULT 'meta',
            external_id VARCHAR(255) NOT NULL,
            campaign_external_id VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            status VARCHAR(50),
            effective_status VARCHAR(50),
            optimization_goal VARCHAR(100),
            billing_event VARCHAR(100),
            bid_strategy VARCHAR(100),
            daily_budget BIGINT,
            lifetime_budget BIGINT,
            budget_remaining BIGINT,
            targeting JSONB DEFAULT '{}'::jsonb,
            destination_type VARCHAR(100),
            learning_stage VARCHAR(50),
            start_time TIMESTAMPTZ,
            end_time TIMESTAMPTZ,
            extra JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ad_sets_tenant_provider_ext
        ON ad_sets (tenant_id, provider, external_id)
        WHERE deleted_at IS NULL
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_ad_sets_tenant ON ad_sets (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ad_sets_campaign ON ad_sets (tenant_id, campaign_external_id)")

    # ── ads ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS ads (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            provider VARCHAR(50) NOT NULL DEFAULT 'meta',
            external_id VARCHAR(255) NOT NULL,
            campaign_external_id VARCHAR(255) NOT NULL,
            ad_set_external_id VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            status VARCHAR(50),
            effective_status VARCHAR(50),
            creative_id VARCHAR(255),
            creative_thumbnail_url TEXT,
            creative_image_url TEXT,
            creative_video_id VARCHAR(255),
            creative_title VARCHAR(500),
            creative_body TEXT,
            creative_cta VARCHAR(100),
            creative_link_url TEXT,
            preview_shareable_link TEXT,
            extra JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_ads_tenant_provider_ext
        ON ads (tenant_id, provider, external_id)
        WHERE deleted_at IS NULL
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_ads_tenant ON ads (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ads_adset ON ads (tenant_id, ad_set_external_id)")

    # ── ad_recommendations ──
    op.execute("""
        CREATE TABLE IF NOT EXISTS ad_recommendations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            provider VARCHAR(50) NOT NULL DEFAULT 'meta',
            source VARCHAR(50) NOT NULL DEFAULT 'account',
            recommendation_type VARCHAR(100) NOT NULL,
            object_ids JSONB DEFAULT '[]'::jsonb,
            title VARCHAR(500),
            body TEXT,
            blame_field VARCHAR(100),
            importance VARCHAR(20),
            confidence VARCHAR(20),
            lift_estimate VARCHAR(100),
            opportunity_score FLOAT,
            url TEXT,
            recommendation_signature VARCHAR(500),
            extra JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            deleted_at TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_ad_recs_tenant ON ad_recommendations (tenant_id)")
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_ad_recs_tenant_type
        ON ad_recommendations (tenant_id, recommendation_type)
        WHERE deleted_at IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ad_recommendations CASCADE")
    op.execute("DROP TABLE IF EXISTS ads CASCADE")
    op.execute("DROP TABLE IF EXISTS ad_sets CASCADE")
    op.execute("DROP TABLE IF EXISTS ad_campaigns CASCADE")
