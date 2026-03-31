"""Add archetype, format_hint, is_lead_magnet columns to products

Revision ID: 018_add_archetype_columns
Revises: 017_normalize_enum_lowercase
Create Date: 2026-03-27
"""
from typing import Sequence, Union
from alembic import op

# revision identifiers
revision = "018_add_archetype_columns"
down_revision = "017_normalize_enum_lowercase"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- New columns ---
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS archetype VARCHAR")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS format_hint VARCHAR")
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS is_lead_magnet BOOLEAN DEFAULT FALSE")

    # --- Backfill archetype from existing type ---
    op.execute("""
        UPDATE products SET archetype = CASE
            WHEN type IN ('free_resource','tripwire_offer','self_paced_course',
                          'physical_merch','content_asset_podcast') THEN 'producto'
            WHEN type IN ('free_webinar_challenge','hybrid_mentorship',
                          'cohort_based_course','group_coaching_program') THEN 'programa'
            WHEN type IN ('vip_day_strategy','one_on_one_private_mentoring','deep_dive_audit',
                          'productized_service','ecommerce_development','monthly_retainer',
                          'performance_rev_share','corporate_training','brand_sponsorship',
                          'keynote_speaking') THEN 'servicio'
            WHEN type IN ('paid_newsletter_subscription','community_lite',
                          'mastermind_network') THEN 'membresia'
            WHEN type IN ('luxury_retreat') THEN 'experiencia'
            ELSE 'producto'
        END
        WHERE archetype IS NULL
    """)

    # --- Backfill format_hint from type (humanize) ---
    op.execute("""
        UPDATE products SET format_hint = REPLACE(type, '_', ' ')
        WHERE format_hint IS NULL AND type IS NOT NULL
    """)

    # --- Backfill is_lead_magnet ---
    op.execute("""
        UPDATE products SET is_lead_magnet = TRUE
        WHERE offer_value_level = 'level_0_free' AND (is_lead_magnet IS NULL OR is_lead_magnet = FALSE)
    """)

    # --- Index for archetype queries ---
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_archetype ON products(archetype)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_products_archetype")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS is_lead_magnet")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS format_hint")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS archetype")
