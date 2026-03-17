"""add lifecycle columns and transitions table

Revision ID: e2f3a4b5c6d7
Revises: d9e0f1a2b3c4
Create Date: 2026-03-15 18:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, None] = "d9e0f1a2b3c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- All operations use raw SQL with IF NOT EXISTS for idempotency ---
    # These columns/tables may already exist in production if they were
    # created outside of alembic before this migration was registered.

    # --- Add new columns to customer_profiles ---
    op.execute("""
        ALTER TABLE customer_profiles ADD COLUMN IF NOT EXISTS lifetime_value FLOAT DEFAULT 0;
        ALTER TABLE customer_profiles ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMPTZ;
        ALTER TABLE customer_profiles ADD COLUMN IF NOT EXISTS is_inactive BOOLEAN DEFAULT false;
        ALTER TABLE customer_profiles ADD COLUMN IF NOT EXISTS first_conversion_at TIMESTAMPTZ;
        ALTER TABLE customer_profiles ADD COLUMN IF NOT EXISTS first_seen_at TIMESTAMPTZ;
        ALTER TABLE customer_profiles ADD COLUMN IF NOT EXISTS lead_source VARCHAR;
        ALTER TABLE customer_profiles ADD COLUMN IF NOT EXISTS lead_source_detail VARCHAR;
    """)

    # Indexes on frequently queried columns
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_customer_profiles_last_activity_at
        ON customer_profiles (last_activity_at);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_customer_profiles_lead_source
        ON customer_profiles (lead_source);
    """)

    # --- Create lifecycle_transitions table ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS lifecycle_transitions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            profile_id UUID NOT NULL REFERENCES customer_profiles(id),
            tenant_id UUID NOT NULL,
            from_stage lifecyclestage,
            to_stage lifecyclestage NOT NULL,
            reason VARCHAR NOT NULL,
            triggered_by VARCHAR NOT NULL,
            score_at_transition FLOAT,
            metadata JSONB DEFAULT '{}',
            occurred_at TIMESTAMPTZ DEFAULT now()
        );
    """)

    # Indexes for lifecycle_transitions
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_lifecycle_transitions_profile_id
        ON lifecycle_transitions (profile_id);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_lifecycle_transitions_tenant_id
        ON lifecycle_transitions (tenant_id);
    """)


def downgrade() -> None:
    # Drop lifecycle_transitions table
    op.drop_index("ix_lifecycle_transitions_tenant_id", table_name="lifecycle_transitions")
    op.drop_index("ix_lifecycle_transitions_profile_id", table_name="lifecycle_transitions")
    op.drop_table("lifecycle_transitions")

    # Drop new customer_profiles columns
    op.drop_index("ix_customer_profiles_lead_source", table_name="customer_profiles")
    op.drop_index("ix_customer_profiles_last_activity_at", table_name="customer_profiles")
    op.drop_column("customer_profiles", "lead_source_detail")
    op.drop_column("customer_profiles", "lead_source")
    op.drop_column("customer_profiles", "first_seen_at")
    op.drop_column("customer_profiles", "first_conversion_at")
    op.drop_column("customer_profiles", "is_inactive")
    op.drop_column("customer_profiles", "last_activity_at")
    op.drop_column("customer_profiles", "lifetime_value")
