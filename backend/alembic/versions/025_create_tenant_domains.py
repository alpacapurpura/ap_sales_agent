"""Create tenant_domains table for Custom Domains feature.

Revision ID: 025_create_tenant_domains
Revises: 024_fix_landing_pages_schema
"""
from alembic import op

revision = "025_create_tenant_domains"
down_revision = "024_fix_landing_pages_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS tenant_domains (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            hostname VARCHAR NOT NULL,
            domain_type VARCHAR NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'pending_verification',
            is_primary BOOLEAN NOT NULL DEFAULT false,
            cloudflare_hostname_id VARCHAR,
            ssl_status VARCHAR,
            verification_method VARCHAR,
            verification_cname_target VARCHAR,
            verification_txt_name VARCHAR,
            verification_txt_value VARCHAR,
            verified_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ
        )
    """)

    # UNIQUE on (tenant_id, hostname) where deleted_at IS NULL
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_tenant_domains_tenant_hostname
        ON tenant_domains (tenant_id, hostname)
        WHERE deleted_at IS NULL
    """)

    # INDEX on hostname for Worker KV lookup
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_tenant_domains_hostname
        ON tenant_domains (hostname)
    """)

    # INDEX on tenant_id
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_tenant_domains_tenant_id
        ON tenant_domains (tenant_id)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tenant_domains")
