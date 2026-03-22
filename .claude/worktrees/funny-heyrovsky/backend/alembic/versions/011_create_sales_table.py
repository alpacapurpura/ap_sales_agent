"""Create sales table for Stage 4 revenue tracking.

Revision ID: 011_create_sales
Revises: 010_referral_nps
Create Date: 2026-03-16
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "011_create_sales"
down_revision = "010_referral_nps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Create enums (idempotent)
    for stmt in [
        "DO $$ BEGIN CREATE TYPE salestatus AS ENUM ('COMPLETED','REFUNDED','PENDING','FAILED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$",
        "DO $$ BEGIN CREATE TYPE salestage AS ENUM ('CONVERSION','EXPANSION'); EXCEPTION WHEN duplicate_object THEN NULL; END $$",
        "DO $$ BEGIN CREATE TYPE paymentmethod AS ENUM ('CREDIT_CARD','WIRE','CASH','STRIPE','PAYPAL','MANUAL'); EXCEPTION WHEN duplicate_object THEN NULL; END $$",
    ]:
        conn.execute(sa.text(stmt))

    # Create table via raw DDL to avoid SQLAlchemy enum creation hooks
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS sales (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            customer_id UUID NOT NULL REFERENCES customer_profiles(id),
            offer_id UUID NOT NULL REFERENCES products(id),
            transaction_id VARCHAR,
            amount FLOAT NOT NULL,
            currency VARCHAR DEFAULT 'USD',
            status salestatus DEFAULT 'PENDING',
            stage salestage NOT NULL,
            source VARCHAR DEFAULT 'MANUAL',
            payment_method paymentmethod,
            metadata_info JSONB DEFAULT '{}',
            occurred_at TIMESTAMPTZ DEFAULT now(),
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        )
    """))

    # Create indexes
    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS ix_sales_tenant_id ON sales (tenant_id)",
        "CREATE INDEX IF NOT EXISTS ix_sales_customer_id ON sales (customer_id)",
        "CREATE INDEX IF NOT EXISTS ix_sales_offer_id ON sales (offer_id)",
        "CREATE INDEX IF NOT EXISTS ix_sales_transaction_id ON sales (transaction_id)",
    ]:
        conn.execute(sa.text(idx_sql))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sales")
    op.execute("DROP TYPE IF EXISTS paymentmethod")
    op.execute("DROP TYPE IF EXISTS salestage")
    op.execute("DROP TYPE IF EXISTS salestatus")
