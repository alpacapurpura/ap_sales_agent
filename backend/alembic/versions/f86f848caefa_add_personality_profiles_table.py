"""add personality_profiles table

Revision ID: f86f848caefa
Revises: f851363921c9
Create Date: 2026-04-14 04:17:03.115369

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f86f848caefa'
down_revision: Union[str, None] = 'f851363921c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS personality_profiles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id UUID NOT NULL,
        offer_id UUID,
        avatar_id UUID,
        name VARCHAR(255) NOT NULL,
        profile_type VARCHAR(20) NOT NULL DEFAULT 'preset',
        preset_key VARCHAR(50),
        is_active BOOLEAN NOT NULL DEFAULT false,
        dimensions JSONB NOT NULL DEFAULT '{}',
        linguistic_patterns JSONB NOT NULL DEFAULT '{}',
        sample_exchanges JSONB NOT NULL DEFAULT '[]',
        negative_constraints JSONB NOT NULL DEFAULT '[]',
        system_instruction TEXT,
        source_metadata JSONB NOT NULL DEFAULT '{}',
        qdrant_collection VARCHAR(100),
        anchor_count INTEGER NOT NULL DEFAULT 0,
        llm_provider VARCHAR(50),
        llm_model VARCHAR(100),
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
        deleted_at TIMESTAMP WITH TIME ZONE
    );
    """)
    op.execute("""
    CREATE INDEX IF NOT EXISTS ix_personality_profiles_tenant
        ON personality_profiles(tenant_id) WHERE deleted_at IS NULL;
    """)
    op.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS uq_personality_profiles_active
        ON personality_profiles(tenant_id)
        WHERE is_active = true AND deleted_at IS NULL AND offer_id IS NULL AND avatar_id IS NULL;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS personality_profiles;")
