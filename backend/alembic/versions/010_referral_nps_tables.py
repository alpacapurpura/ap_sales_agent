"""Add referral_codes, nps_surveys, nps_responses tables for evangelization stage.

Revision ID: 010_referral_nps
Revises: ab8346fd2c09
Create Date: 2026-03-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "010_referral_nps"
down_revision = "ab8346fd2c09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- referral_codes ---
    op.create_table(
        "referral_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customer_profiles.id"),
            nullable=False,
        ),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("source", sa.String(), server_default="internal"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_referral_codes_tenant_id", "referral_codes", ["tenant_id"])
    op.create_index("ix_referral_codes_customer_id", "referral_codes", ["customer_id"])
    op.create_index("ix_referral_codes_code", "referral_codes", ["code"], unique=True)
    op.create_index(
        "ix_referral_codes_tenant_customer", "referral_codes", ["tenant_id", "customer_id"]
    )

    # --- nps_surveys ---
    op.create_table(
        "nps_surveys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(), nullable=False, unique=True),
        sa.Column("offer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customer_profiles.id"),
            nullable=True,
        ),
        sa.Column("delivery_channel", sa.String(), server_default="universal_link"),
        sa.Column("status", sa.String(), server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_nps_surveys_tenant_id", "nps_surveys", ["tenant_id"])
    op.create_index("ix_nps_surveys_token", "nps_surveys", ["token"], unique=True)
    op.create_index(
        "ix_nps_surveys_tenant_customer", "nps_surveys", ["tenant_id", "customer_id"]
    )

    # --- nps_responses ---
    op.create_table(
        "nps_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "survey_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("nps_surveys.id"),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customer_profiles.id"),
            nullable=False,
        ),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("feedback_text", sa.String(), nullable=True),
        sa.Column("testimonial_text", sa.String(), nullable=True),
        sa.Column("testimonial_audio_url", sa.String(), nullable=True),
        sa.Column("consent_public_use", sa.Boolean(), server_default="false"),
        sa.Column("responded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_nps_responses_tenant_id", "nps_responses", ["tenant_id"])
    op.create_index("ix_nps_responses_customer_id", "nps_responses", ["customer_id"])
    op.create_index(
        "ix_nps_responses_tenant_survey", "nps_responses", ["tenant_id", "survey_id"]
    )


def downgrade() -> None:
    op.drop_table("nps_responses")
    op.drop_table("nps_surveys")
    op.drop_table("referral_codes")
