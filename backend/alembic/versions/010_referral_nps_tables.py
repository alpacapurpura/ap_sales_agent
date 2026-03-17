"""Add referral_codes, nps_surveys, nps_responses tables for evangelization stage.

Revision ID: 010_referral_nps
Revises: ab8346fd2c09
Create Date: 2026-03-16
"""
from alembic import op

# revision identifiers
revision = "010_referral_nps"
down_revision = "ab8346fd2c09"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- referral_codes ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS referral_codes (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            customer_id UUID NOT NULL REFERENCES customer_profiles(id),
            code VARCHAR NOT NULL UNIQUE,
            source VARCHAR DEFAULT 'internal',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_referral_codes_tenant_id ON referral_codes (tenant_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_referral_codes_customer_id ON referral_codes (customer_id);")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_referral_codes_code ON referral_codes (code);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_referral_codes_tenant_customer ON referral_codes (tenant_id, customer_id);")

    # --- nps_surveys ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS nps_surveys (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            token VARCHAR NOT NULL UNIQUE,
            offer_id UUID,
            customer_id UUID REFERENCES customer_profiles(id),
            delivery_channel VARCHAR DEFAULT 'universal_link',
            status VARCHAR DEFAULT 'pending',
            created_at TIMESTAMPTZ DEFAULT now(),
            sent_at TIMESTAMPTZ,
            expires_at TIMESTAMPTZ
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_nps_surveys_tenant_id ON nps_surveys (tenant_id);")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_nps_surveys_token ON nps_surveys (token);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nps_surveys_tenant_customer ON nps_surveys (tenant_id, customer_id);")

    # --- nps_responses ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS nps_responses (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            survey_id UUID NOT NULL REFERENCES nps_surveys(id),
            customer_id UUID NOT NULL REFERENCES customer_profiles(id),
            score INTEGER NOT NULL,
            feedback_text VARCHAR,
            testimonial_text VARCHAR,
            testimonial_audio_url VARCHAR,
            consent_public_use BOOLEAN DEFAULT false,
            responded_at TIMESTAMPTZ DEFAULT now()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_nps_responses_tenant_id ON nps_responses (tenant_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nps_responses_customer_id ON nps_responses (customer_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_nps_responses_tenant_survey ON nps_responses (tenant_id, survey_id);")


def downgrade() -> None:
    op.drop_table("nps_responses")
    op.drop_table("nps_surveys")
    op.drop_table("referral_codes")
