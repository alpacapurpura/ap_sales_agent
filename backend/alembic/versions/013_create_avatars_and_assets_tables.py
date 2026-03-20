"""Create avatars and assets tables.

Revision ID: 013_create_avatars_assets
Revises: 012_file_path_nullable
Create Date: 2026-03-19
"""
from alembic import op

# revision identifiers
revision = "013_create_avatars_assets"
down_revision = "012_file_path_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS avatars (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID REFERENCES tenants(id),
            user_id UUID,
            name VARCHAR NOT NULL,
            scope VARCHAR DEFAULT 'GLOBAL',
            icp_description TEXT,
            anti_avatar TEXT,
            voice_tone_config JSONB DEFAULT '{}',
            is_default BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        );

        CREATE INDEX IF NOT EXISTS ix_avatars_tenant_id ON avatars(tenant_id);
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID REFERENCES tenants(id),
            offer_id UUID REFERENCES products(id),
            type VARCHAR DEFAULT 'IMAGE',
            filename VARCHAR NOT NULL,
            mime_type VARCHAR,
            storage_provider VARCHAR DEFAULT 'LOCAL',
            storage_path VARCHAR,
            public_url VARCHAR NOT NULL,
            file_path VARCHAR DEFAULT '',
            user_description TEXT,
            ai_metadata JSONB DEFAULT '{}',
            ai_description TEXT,
            ai_colors JSONB DEFAULT '[]',
            status VARCHAR DEFAULT 'processing',
            error_message TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        );

        CREATE INDEX IF NOT EXISTS ix_assets_tenant_id ON assets(tenant_id);
        CREATE INDEX IF NOT EXISTS ix_assets_offer_id ON assets(offer_id);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS assets;")
    op.execute("DROP TABLE IF EXISTS avatars;")
