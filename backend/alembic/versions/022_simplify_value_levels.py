"""Simplify 7 OfferValueLevel values into 5 Value Ladder groups.

Revision ID: 022_value_levels
Revises: 021_drop_type
"""
from alembic import op

revision = "022_value_levels"
down_revision = "021_drop_type"
branch_labels = None
depends_on = None


def upgrade():
    # Idempotent: only updates rows that still have old values
    op.execute("""
        UPDATE products SET offer_value_level = CASE
            WHEN offer_value_level = 'level_0_free' THEN 'lead_magnet'
            WHEN offer_value_level = 'level_1_low_ticket' THEN 'activacion'
            WHEN offer_value_level = 'level_2_mid_ticket' THEN 'transformacion'
            WHEN offer_value_level = 'level_3_high_ticket' THEN 'transformacion'
            WHEN offer_value_level = 'level_4_recurring' THEN 'transformacion'
            WHEN offer_value_level = 'level_5_ultra_high' THEN 'maximizacion'
            WHEN offer_value_level = 'level_6_corporate' THEN 'corporativo'
            ELSE offer_value_level
        END
        WHERE offer_value_level IN (
            'level_0_free', 'level_1_low_ticket', 'level_2_mid_ticket',
            'level_3_high_ticket', 'level_4_recurring', 'level_5_ultra_high',
            'level_6_corporate'
        )
    """)


def downgrade():
    # Best-effort reverse: map back to closest original values
    op.execute("""
        UPDATE products SET offer_value_level = CASE
            WHEN offer_value_level = 'lead_magnet' THEN 'level_0_free'
            WHEN offer_value_level = 'activacion' THEN 'level_1_low_ticket'
            WHEN offer_value_level = 'transformacion' THEN 'level_2_mid_ticket'
            WHEN offer_value_level = 'maximizacion' THEN 'level_5_ultra_high'
            WHEN offer_value_level = 'corporativo' THEN 'level_6_corporate'
            ELSE offer_value_level
        END
        WHERE offer_value_level IN (
            'lead_magnet', 'activacion', 'transformacion',
            'maximizacion', 'corporativo'
        )
    """)
