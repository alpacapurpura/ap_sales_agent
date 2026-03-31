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
    # Status to lowercase
    op.execute("UPDATE products SET status = LOWER(status) WHERE status IS NOT NULL AND status != LOWER(status)")
    # Type to lowercase
    op.execute("UPDATE products SET type = LOWER(type) WHERE type IS NOT NULL AND type != LOWER(type)")
    # Fix legacy 1on1
    op.execute("UPDATE products SET type = 'one_on_one_private_mentoring' WHERE LOWER(type) = '1on1_private_mentoring'")
    # delivery_model to lowercase
    op.execute("UPDATE products SET delivery_model = LOWER(delivery_model) WHERE delivery_model IS NOT NULL AND delivery_model != LOWER(delivery_model)")
    # guarantee_type normalize
    op.execute("UPDATE products SET guarantee_type = LOWER(guarantee_type) WHERE guarantee_type IS NOT NULL AND guarantee_type != LOWER(guarantee_type)")
    op.execute("UPDATE products SET guarantee_type = 'none' WHERE guarantee_type = 'no_refunds'")
    # offer_value_level to lowercase
    op.execute("UPDATE products SET offer_value_level = LOWER(offer_value_level) WHERE offer_value_level IS NOT NULL AND offer_value_level != LOWER(offer_value_level)")


def downgrade() -> None:
    # Reversing lowercase normalization is not meaningful
    pass
