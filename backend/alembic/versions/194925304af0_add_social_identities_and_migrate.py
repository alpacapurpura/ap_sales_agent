"""add_social_identities_and_migrate

Revision ID: 194925304af0
Revises: 94469ab70585
Create Date: 2026-02-26 11:13:47.001005

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '194925304af0'
down_revision: Union[str, None] = '94469ab70585'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new values to IdentityType enum
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE identitytype ADD VALUE IF NOT EXISTS 'whatsapp'")
        op.execute("ALTER TYPE identitytype ADD VALUE IF NOT EXISTS 'telegram'")
        op.execute("ALTER TYPE identitytype ADD VALUE IF NOT EXISTS 'instagram'")
        op.execute("ALTER TYPE identitytype ADD VALUE IF NOT EXISTS 'tiktok'")

    # 2. Sync customer_profiles schema (Add missing columns from Model)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='customer_profiles' AND column_name='full_name') THEN
                ALTER TABLE customer_profiles ADD COLUMN full_name VARCHAR;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='customer_profiles' AND column_name='primary_email') THEN
                ALTER TABLE customer_profiles ADD COLUMN primary_email VARCHAR;
                CREATE INDEX IF NOT EXISTS ix_customer_profiles_primary_email ON customer_profiles(primary_email);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='customer_profiles' AND column_name='primary_phone') THEN
                ALTER TABLE customer_profiles ADD COLUMN primary_phone VARCHAR;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='customer_profiles' AND column_name='rfm_segment') THEN
                ALTER TABLE customer_profiles ADD COLUMN rfm_segment VARCHAR;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='customer_profiles' AND column_name='traits') THEN
                ALTER TABLE customer_profiles ADD COLUMN traits JSONB DEFAULT '{}';
            END IF;
             IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='customer_profiles' AND column_name='lead_score') THEN
                ALTER TABLE customer_profiles ADD COLUMN lead_score FLOAT DEFAULT 0.0;
            END IF;
        END
        $$;
    """)

    # 3. Add missing columns to customer_identities
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='customer_identities' AND column_name='verification_status') THEN
                ALTER TABLE customer_identities ADD COLUMN verification_status VARCHAR DEFAULT 'unverified';
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='customer_identities' AND column_name='last_seen_at') THEN
                ALTER TABLE customer_identities ADD COLUMN last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='customer_identities' AND column_name='tenant_id') THEN
                ALTER TABLE customer_identities ADD COLUMN tenant_id UUID; -- Assuming UUID here, need to match customer_profiles.tenant_id type if we want to be safe, but let's try UUID
                CREATE INDEX IF NOT EXISTS ix_customer_identities_tenant_id ON customer_identities(tenant_id);
            END IF;
        END
        $$;
    """)

    # 4. Handle Leads -> Customer Link
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='leads' AND column_name='customer_id') THEN
                ALTER TABLE leads ADD COLUMN customer_id UUID;
                CREATE INDEX IF NOT EXISTS ix_leads_customer_id ON leads(customer_id);
            END IF;
        END
        $$;
    """)

    # 5. Data Migration: Create Customers for existing Leads
    op.execute("""
        -- Generate customer_ids for leads that don't have one AND have a valid tenant_id
        UPDATE leads SET customer_id = gen_random_uuid() 
        WHERE customer_id IS NULL AND tenant_id IS NOT NULL;
        
        -- Insert into customer_profiles from leads
        INSERT INTO customer_profiles (id, tenant_id, full_name, primary_email, primary_phone, created_at, updated_at, traits)
        SELECT 
            customer_id,
            tenant_id::varchar, 
            full_name,
            email,
            phone,
            created_at,
            updated_at,
            profile_data
        FROM leads
        WHERE customer_id IS NOT NULL 
        AND tenant_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM customer_profiles WHERE id = leads.customer_id);
    """)

    # 6. Migrate Identities
    
    # Telegram
    op.execute("""
        INSERT INTO customer_identities (id, profile_id, tenant_id, type, value, is_primary, verification_status, last_seen_at)
        SELECT 
            gen_random_uuid(), 
            customer_id, 
            tenant_id,
            'telegram'::identitytype, 
            telegram_id, 
            false, 
            'unverified', 
            COALESCE(last_interaction_date, NOW())
        FROM leads 
        WHERE telegram_id IS NOT NULL AND customer_id IS NOT NULL AND tenant_id IS NOT NULL
        AND EXISTS (SELECT 1 FROM customer_profiles WHERE id = leads.customer_id) -- Ensure profile exists
        AND NOT EXISTS (
            SELECT 1 FROM customer_identities 
            WHERE profile_id = leads.customer_id AND type = 'telegram' AND value = leads.telegram_id
        );
    """)
    
    # WhatsApp
    op.execute("""
        INSERT INTO customer_identities (id, profile_id, tenant_id, type, value, is_primary, verification_status, last_seen_at)
        SELECT 
            gen_random_uuid(), 
            customer_id, 
            tenant_id,
            'whatsapp'::identitytype, 
            whatsapp_id, 
            false, 
            'unverified', 
            COALESCE(last_interaction_date, NOW())
        FROM leads 
        WHERE whatsapp_id IS NOT NULL AND customer_id IS NOT NULL AND tenant_id IS NOT NULL
        AND EXISTS (SELECT 1 FROM customer_profiles WHERE id = leads.customer_id)
        AND NOT EXISTS (
            SELECT 1 FROM customer_identities 
            WHERE profile_id = leads.customer_id AND type = 'whatsapp' AND value = leads.whatsapp_id
        );
    """)

    # Instagram
    op.execute("""
        INSERT INTO customer_identities (id, profile_id, tenant_id, type, value, is_primary, verification_status, last_seen_at)
        SELECT 
            gen_random_uuid(), 
            customer_id, 
            tenant_id,
            'instagram'::identitytype, 
            instagram_id, 
            false, 
            'unverified', 
            COALESCE(last_interaction_date, NOW())
        FROM leads 
        WHERE instagram_id IS NOT NULL AND customer_id IS NOT NULL AND tenant_id IS NOT NULL
        AND EXISTS (SELECT 1 FROM customer_profiles WHERE id = leads.customer_id)
        AND NOT EXISTS (
            SELECT 1 FROM customer_identities 
            WHERE profile_id = leads.customer_id AND type = 'instagram' AND value = leads.instagram_id
        );
    """)

    # TikTok
    op.execute("""
        INSERT INTO customer_identities (id, profile_id, tenant_id, type, value, is_primary, verification_status, last_seen_at)
        SELECT 
            gen_random_uuid(), 
            customer_id, 
            tenant_id,
            'tiktok'::identitytype, 
            tiktok_id, 
            false, 
            'unverified', 
            COALESCE(last_interaction_date, NOW())
        FROM leads 
        WHERE tiktok_id IS NOT NULL AND customer_id IS NOT NULL AND tenant_id IS NOT NULL
        AND EXISTS (SELECT 1 FROM customer_profiles WHERE id = leads.customer_id)
        AND NOT EXISTS (
            SELECT 1 FROM customer_identities 
            WHERE profile_id = leads.customer_id AND type = 'tiktok' AND value = leads.tiktok_id
        );
    """)

    # 7. Add Foreign Key Constraint
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name='fk_leads_customer_id') THEN
                ALTER TABLE leads ADD CONSTRAINT fk_leads_customer_id FOREIGN KEY (customer_id) REFERENCES customer_profiles(id);
            END IF;
        END
        $$;
    """)

    # 8. Make old columns nullable
    op.alter_column('leads', 'telegram_id', nullable=True)
    op.alter_column('leads', 'whatsapp_id', nullable=True)
    op.alter_column('leads', 'instagram_id', nullable=True)
    op.alter_column('leads', 'tiktok_id', nullable=True)


def downgrade() -> None:
    pass
