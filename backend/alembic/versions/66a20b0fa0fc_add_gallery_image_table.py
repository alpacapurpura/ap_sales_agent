"""add_gallery_image_table

Revision ID: 66a20b0fa0fc
Revises: a1b2c3d4e5f6
Create Date: 2026-02-10 13:31:54.056326

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '66a20b0fa0fc'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create gallery_images table
    op.execute("""
        CREATE TABLE IF NOT EXISTS gallery_images (
            id UUID NOT NULL PRIMARY KEY,
            tenant_id UUID REFERENCES tenants(id),
            filename VARCHAR NOT NULL,
            file_path VARCHAR NOT NULL,
            public_url VARCHAR NOT NULL,
            user_description TEXT,
            ai_description TEXT,
            ai_colors JSONB,
            status VARCHAR,
            error_message TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ
        )
    """)

    # Add columns to agent_traces (skip if table doesn't exist)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = 'agent_traces') THEN
                ALTER TABLE agent_traces ADD COLUMN IF NOT EXISTS action VARCHAR;
                ALTER TABLE agent_traces ADD COLUMN IF NOT EXISTS reward FLOAT;
                ALTER TABLE agent_traces ADD COLUMN IF NOT EXISTS feedback TEXT;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE agent_traces DROP COLUMN IF EXISTS feedback")
    op.execute("ALTER TABLE agent_traces DROP COLUMN IF EXISTS reward")
    op.execute("ALTER TABLE agent_traces DROP COLUMN IF EXISTS action")
    op.execute("DROP TABLE IF EXISTS gallery_images")
