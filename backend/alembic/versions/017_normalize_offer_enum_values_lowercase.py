"""Normalize offer enum values to lowercase

Revision ID: 017_normalize_enum_lowercase
Revises: 016_user_tenant_soft_delete
Create Date: 2026-03-27
"""
from typing import Sequence, Union
from alembic import op

# revision identifiers
revision = "017_normalize_enum_lowercase"
down_revision = "016_user_tenant_soft_delete"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Status to lowercase (status column is safe — always present)
    op.execute("""
        UPDATE products SET status = LOWER(status)
        WHERE status IS NOT NULL AND status != LOWER(status)
    """)

    # Type to lowercase — column may not exist on fresh DB
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'type'
            ) THEN
                UPDATE products SET type = LOWER(type)
                WHERE type IS NOT NULL AND type != LOWER(type);

                -- Fix legacy 1on1
                UPDATE products SET type = 'one_on_one_private_mentoring'
                WHERE LOWER(type) = '1on1_private_mentoring';
            END IF;
        END $$
    """)

    # delivery_model to lowercase
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'delivery_model'
            ) THEN
                UPDATE products SET delivery_model = LOWER(delivery_model)
                WHERE delivery_model IS NOT NULL AND delivery_model != LOWER(delivery_model);
            END IF;
        END $$
    """)

    # guarantee_type normalize
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'guarantee_type'
            ) THEN
                UPDATE products SET guarantee_type = LOWER(guarantee_type)
                WHERE guarantee_type IS NOT NULL AND guarantee_type != LOWER(guarantee_type);

                UPDATE products SET guarantee_type = 'none'
                WHERE guarantee_type = 'no_refunds';
            END IF;
        END $$
    """)

    # offer_value_level to lowercase
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'products' AND column_name = 'offer_value_level'
            ) THEN
                UPDATE products SET offer_value_level = LOWER(offer_value_level)
                WHERE offer_value_level IS NOT NULL AND offer_value_level != LOWER(offer_value_level);
            END IF;
        END $$
    """)


def downgrade() -> None:
    # Reversing lowercase normalization is not meaningful
    pass
