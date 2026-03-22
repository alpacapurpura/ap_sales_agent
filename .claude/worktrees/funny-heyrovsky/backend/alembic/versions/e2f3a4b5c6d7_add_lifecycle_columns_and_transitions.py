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
    # --- Add new columns to customer_profiles ---
    op.add_column(
        "customer_profiles",
        sa.Column("lifetime_value", sa.Float(), server_default="0", nullable=True),
    )
    op.add_column(
        "customer_profiles",
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "customer_profiles",
        sa.Column("is_inactive", sa.Boolean(), server_default="false", nullable=True),
    )
    op.add_column(
        "customer_profiles",
        sa.Column("first_conversion_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "customer_profiles",
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "customer_profiles",
        sa.Column("lead_source", sa.String(), nullable=True),
    )
    op.add_column(
        "customer_profiles",
        sa.Column("lead_source_detail", sa.String(), nullable=True),
    )

    # Indexes on frequently queried columns
    op.create_index(
        "ix_customer_profiles_last_activity_at",
        "customer_profiles",
        ["last_activity_at"],
    )
    op.create_index(
        "ix_customer_profiles_lead_source",
        "customer_profiles",
        ["lead_source"],
    )

    # --- Create lifecycle_transitions table ---
    # Note: LifecycleStage enum already exists from customer_profiles table.
    # triggered_by uses String (not PG enum) to avoid ALTER TYPE issues.
    op.create_table(
        "lifecycle_transitions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customer_profiles.id"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "from_stage",
            sa.Enum(
                "subscriber",
                "lead",
                "mql",
                "sql",
                "opportunity",
                "customer",
                "evangelist",
                "churned",
                name="lifecyclestage",
                create_type=False,  # Enum already exists
            ),
            nullable=True,
        ),
        sa.Column(
            "to_stage",
            sa.Enum(
                "subscriber",
                "lead",
                "mql",
                "sql",
                "opportunity",
                "customer",
                "evangelist",
                "churned",
                name="lifecyclestage",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("reason", sa.String(), nullable=False),
        sa.Column("triggered_by", sa.String(), nullable=False),
        sa.Column("score_at_transition", sa.Float(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Indexes for lifecycle_transitions
    op.create_index(
        "ix_lifecycle_transitions_profile_id",
        "lifecycle_transitions",
        ["profile_id"],
    )
    op.create_index(
        "ix_lifecycle_transitions_tenant_id",
        "lifecycle_transitions",
        ["tenant_id"],
    )


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
