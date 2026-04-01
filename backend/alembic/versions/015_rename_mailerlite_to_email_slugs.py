"""Rename mailerlite channel slugs to provider-agnostic email-* slugs.

Migrates channel_slug values in official_metrics, staging_metrics, and
metric_aggregations from 'mailerlite' to 'email-nurture' (the default stage).
Also adds stage_group_mapping to existing mailerlite channel_connections config.

Revision ID: 015_email_slugs
Revises: d4e5f6a7b8c9
Create Date: 2026-03-25
"""
from alembic import op

# revision identifiers
revision = "015_email_slugs"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Rename channel_slug 'mailerlite' → 'email-nurture' in metrics tables ---
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'official_metrics') THEN
                UPDATE official_metrics
                SET channel_slug = 'email-nurture'
                WHERE channel_slug = 'mailerlite'
                  AND provider = 'mailerlite'
                  AND NOT EXISTS (
                      SELECT 1 FROM official_metrics om2
                      WHERE om2.tenant_id = official_metrics.tenant_id
                        AND om2.provider = official_metrics.provider
                        AND om2.channel_slug = 'email-nurture'
                        AND om2.metric_name = official_metrics.metric_name
                        AND om2.metric_date = official_metrics.metric_date
                  );
                DELETE FROM official_metrics
                WHERE channel_slug = 'mailerlite'
                  AND provider = 'mailerlite';
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'staging_metrics') THEN
                UPDATE staging_metrics
                SET channel_slug = 'email-nurture'
                WHERE channel_slug = 'mailerlite'
                  AND provider = 'mailerlite';
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'metric_aggregations') THEN
                UPDATE metric_aggregations
                SET channel_slug = 'email-nurture'
                WHERE channel_slug = 'mailerlite';
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'channel_connections') THEN
                UPDATE channel_connections
                SET config = config || '{"stage_group_mapping": {}, "known_groups": []}'::jsonb
                WHERE channel_type = 'mailerlite'
                  AND NOT config ? 'stage_group_mapping';
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'official_metrics') THEN
                UPDATE official_metrics SET channel_slug = 'mailerlite'
                WHERE channel_slug = 'email-nurture' AND provider = 'mailerlite';
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'staging_metrics') THEN
                UPDATE staging_metrics SET channel_slug = 'mailerlite'
                WHERE channel_slug = 'email-nurture' AND provider = 'mailerlite';
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'metric_aggregations') THEN
                UPDATE metric_aggregations SET channel_slug = 'mailerlite'
                WHERE channel_slug = 'email-nurture';
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'channel_connections') THEN
                UPDATE channel_connections
                SET config = config - 'stage_group_mapping' - 'known_groups'
                WHERE channel_type = 'mailerlite' AND config ? 'stage_group_mapping';
            END IF;
        END $$;
    """)
