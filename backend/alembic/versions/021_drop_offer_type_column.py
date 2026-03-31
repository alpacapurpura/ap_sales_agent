"""Drop OfferType column — archetype is now the only classification.

Revision ID: 021_drop_type
Revises: 020_agent_checkpoints
"""
from alembic import op

revision = "021_drop_type"
down_revision = "020_agent_checkpoints"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Backfill archetype from type where NULL (only if type column exists)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'type'
            ) THEN
                UPDATE products SET archetype = CASE
                    WHEN type IN ('free_resource','tripwire_offer','self_paced_course',
                                  'physical_merch','content_asset_podcast') THEN 'producto'
                    WHEN type IN ('free_webinar_challenge','hybrid_mentorship',
                                  'cohort_based_course','group_coaching_program','group_program') THEN 'programa'
                    WHEN type IN ('vip_day_strategy','one_on_one_private_mentoring','deep_dive_audit',
                                  'productized_service','ecommerce_development','monthly_retainer',
                                  'performance_rev_share','corporate_training','brand_sponsorship',
                                  'keynote_speaking') THEN 'servicio'
                    WHEN type IN ('paid_newsletter_subscription','community_lite',
                                  'mastermind_network') THEN 'membresia'
                    WHEN type IN ('luxury_retreat') THEN 'experiencia'
                    ELSE 'producto'
                END
                WHERE archetype IS NULL;
            END IF;
        END $$
    """)

    # 2. Preserve type as format_hint for rows without one (only if type column exists)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'type'
            ) THEN
                UPDATE products SET format_hint = REPLACE(type, '_', ' ')
                WHERE format_hint IS NULL AND type IS NOT NULL;
            END IF;
        END $$
    """)

    # 3. Backfill value_level where NULL (only if type column exists)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'type'
            ) THEN
                UPDATE products SET offer_value_level = CASE
                    WHEN type IN ('free_resource','community_lite','content_asset_podcast',
                                  'free_webinar_challenge') THEN 'level_0_free'
                    WHEN type IN ('tripwire_offer','self_paced_course',
                                  'paid_newsletter_subscription','physical_merch') THEN 'level_1_low_ticket'
                    WHEN type IN ('hybrid_mentorship','cohort_based_course',
                                  'group_coaching_program','group_program') THEN 'level_2_mid_ticket'
                    WHEN type IN ('vip_day_strategy','one_on_one_private_mentoring',
                                  'deep_dive_audit') THEN 'level_3_high_ticket'
                    WHEN type IN ('productized_service','ecommerce_development',
                                  'monthly_retainer','performance_rev_share') THEN 'level_4_recurring'
                    WHEN type IN ('mastermind_network','luxury_retreat') THEN 'level_5_ultra_high'
                    WHEN type IN ('corporate_training','brand_sponsorship',
                                  'keynote_speaking') THEN 'level_6_corporate'
                    ELSE 'level_1_low_ticket'
                END
                WHERE offer_value_level IS NULL AND type IS NOT NULL;
            END IF;
        END $$
    """)

    # 4. Make archetype NOT NULL (idempotent — safe to run if already NOT NULL)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'archetype'
                  AND is_nullable = 'YES'
            ) THEN
                -- Set default for any remaining NULLs before adding constraint
                UPDATE products SET archetype = 'producto' WHERE archetype IS NULL;
                ALTER TABLE products ALTER COLUMN archetype SET NOT NULL;
            END IF;
        END $$
    """)

    # 5. Drop the type column (already idempotent)
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS type")


def downgrade():
    # Recreate column (idempotent)
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS type VARCHAR")

    # Backfill type from archetype
    op.execute("""
        UPDATE products SET type = CASE archetype
            WHEN 'producto' THEN 'self_paced_course'
            WHEN 'programa' THEN 'group_program'
            WHEN 'servicio' THEN 'productized_service'
            WHEN 'membresia' THEN 'paid_newsletter_subscription'
            WHEN 'experiencia' THEN 'luxury_retreat'
            ELSE 'free_resource'
        END
        WHERE type IS NULL
    """)

    # Make type NOT NULL (idempotent)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'type'
                  AND is_nullable = 'YES'
            ) THEN
                ALTER TABLE products ALTER COLUMN type SET NOT NULL;
            END IF;
        END $$
    """)

    # Make archetype nullable again (idempotent)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'archetype'
                  AND is_nullable = 'NO'
            ) THEN
                ALTER TABLE products ALTER COLUMN archetype DROP NOT NULL;
            END IF;
        END $$
    """)
