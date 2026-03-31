"""refactor_offer_and_journey_final

Revision ID: 9c6fc3c2980b
Revises: 16a58268fd71
Create Date: 2026-02-02 21:46:20.150218

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9c6fc3c2980b'
down_revision: Union[str, None] = '16a58268fd71'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. RENAME enrollments -> journey_progress (only if enrollments exists and journey_progress does not)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'enrollments')
               AND NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'journey_progress')
            THEN
                ALTER TABLE enrollments RENAME TO journey_progress;
            END IF;
        END $$;
    """)

    # 2. Add new columns to journey_progress (skip if table doesn't exist on fresh DB)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = 'journey_progress') THEN
                ALTER TABLE journey_progress ADD COLUMN IF NOT EXISTS product_line VARCHAR;
                ALTER TABLE journey_progress ADD COLUMN IF NOT EXISTS funnel_entry_point VARCHAR;
                ALTER TABLE journey_progress ADD COLUMN IF NOT EXISTS deal_value_potential FLOAT DEFAULT 0.0;
                ALTER TABLE journey_progress ADD COLUMN IF NOT EXISTS objection_status VARCHAR;
            END IF;
        END $$;
    """)

    # 3. Handle avatar_definitions FK rename (skip if table doesn't exist — orphaned)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = 'avatar_definitions') THEN
                -- Drop old FK if exists
                IF EXISTS (
                    SELECT 1 FROM information_schema.table_constraints
                    WHERE constraint_name = 'avatar_definitions_user_id_fkey'
                      AND table_name = 'avatar_definitions'
                ) THEN
                    ALTER TABLE avatar_definitions DROP CONSTRAINT avatar_definitions_user_id_fkey;
                END IF;
                -- Add new FK if not exists
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.key_column_usage kcu
                    JOIN information_schema.referential_constraints rc
                        ON kcu.constraint_name = rc.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                        ON rc.unique_constraint_name = ccu.constraint_name
                    WHERE kcu.table_name = 'avatar_definitions'
                      AND kcu.column_name = 'user_id'
                      AND ccu.table_name = 'users'
                ) THEN
                    ALTER TABLE avatar_definitions
                        ADD CONSTRAINT avatar_definitions_user_id_fkey_users
                        FOREIGN KEY (user_id) REFERENCES users(id);
                END IF;
            END IF;
        END $$;
    """)

    # 4. Add new columns to leads (skip if table doesn't exist)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = 'leads') THEN
                ALTER TABLE leads ADD COLUMN IF NOT EXISTS social_handle_main VARCHAR;
                ALTER TABLE leads ADD COLUMN IF NOT EXISTS timezone VARCHAR;
                ALTER TABLE leads ADD COLUMN IF NOT EXISTS fit_score INTEGER;
                ALTER TABLE leads ADD COLUMN IF NOT EXISTS intent_score INTEGER;
                ALTER TABLE leads ADD COLUMN IF NOT EXISTS temperature VARCHAR;
                ALTER TABLE leads ADD COLUMN IF NOT EXISTS is_blacklisted BOOLEAN;
                ALTER TABLE leads ADD COLUMN IF NOT EXISTS last_interaction_date TIMESTAMPTZ;
                ALTER TABLE leads ADD COLUMN IF NOT EXISTS next_scheduled_action TIMESTAMPTZ;
                ALTER TABLE leads ADD COLUMN IF NOT EXISTS conversation_summary TEXT;
                ALTER TABLE leads ADD COLUMN IF NOT EXISTS key_objections_history JSONB;
            END IF;
        END $$;
    """)

    # 5. Handle leads index/constraint changes
    op.execute("DROP INDEX IF EXISTS ix_leads_api_id")
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'users_email_key' AND table_name = 'leads'
            ) THEN
                ALTER TABLE leads DROP CONSTRAINT users_email_key;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'users_phone_key' AND table_name = 'leads'
            ) THEN
                ALTER TABLE leads DROP CONSTRAINT users_phone_key;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = 'leads')
               AND NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE table_name = 'leads'
                  AND constraint_type = 'UNIQUE'
                  AND constraint_name = 'uq_leads_api_id'
            ) THEN
                ALTER TABLE leads ADD CONSTRAINT uq_leads_api_id UNIQUE (api_id);
            END IF;
        END $$;
    """)

    # 6. Add new columns to products (skip if table doesn't exist)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables
                       WHERE table_schema = 'public' AND table_name = 'products') THEN
                ALTER TABLE products ADD COLUMN IF NOT EXISTS internal_sku VARCHAR;
                ALTER TABLE products ADD COLUMN IF NOT EXISTS delivery_model VARCHAR;
                ALTER TABLE products ADD COLUMN IF NOT EXISTS headline_promise VARCHAR;
                ALTER TABLE products ADD COLUMN IF NOT EXISTS target_avatar_match JSONB;
                ALTER TABLE products ADD COLUMN IF NOT EXISTS requires_application BOOLEAN;
                ALTER TABLE products ADD COLUMN IF NOT EXISTS min_financial_capacity VARCHAR;
                ALTER TABLE products ADD COLUMN IF NOT EXISTS currency VARCHAR;
                ALTER TABLE products ADD COLUMN IF NOT EXISTS guarantee_type VARCHAR;
                ALTER TABLE products ADD COLUMN IF NOT EXISTS upsell_product_id UUID;
            END IF;
        END $$;
    """)

    # 7. FK for upsell_product_id (skip if table/column doesn't exist)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns
                       WHERE table_schema = 'public' AND table_name = 'products'
                         AND column_name = 'upsell_product_id')
               AND NOT EXISTS (
                SELECT 1 FROM information_schema.key_column_usage kcu
                JOIN information_schema.referential_constraints rc
                    ON kcu.constraint_name = rc.constraint_name
                WHERE kcu.table_name = 'products'
                  AND kcu.column_name = 'upsell_product_id'
            ) THEN
                ALTER TABLE products
                    ADD CONSTRAINT fk_products_upsell_product_id
                    FOREIGN KEY (upsell_product_id) REFERENCES products(id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Drop products FK + columns
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_products_upsell_product_id'
                  AND table_name = 'products'
            ) THEN
                ALTER TABLE products DROP CONSTRAINT fk_products_upsell_product_id;
            END IF;
        END $$;
    """)
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS upsell_product_id")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS guarantee_type")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS currency")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS min_financial_capacity")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS requires_application")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS target_avatar_match")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS headline_promise")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS delivery_model")
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS internal_sku")

    # Restore leads constraints
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'uq_leads_api_id' AND table_name = 'leads'
            ) THEN
                ALTER TABLE leads DROP CONSTRAINT uq_leads_api_id;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'users_phone_key' AND table_name = 'leads'
            ) THEN
                ALTER TABLE leads ADD CONSTRAINT users_phone_key UNIQUE (phone);
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'users_email_key' AND table_name = 'leads'
            ) THEN
                ALTER TABLE leads ADD CONSTRAINT users_email_key UNIQUE (email);
            END IF;
        END $$;
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_leads_api_id ON leads (api_id)")

    # Drop leads columns
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS key_objections_history")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS conversation_summary")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS next_scheduled_action")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS last_interaction_date")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS is_blacklisted")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS temperature")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS intent_score")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS fit_score")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS timezone")
    op.execute("ALTER TABLE leads DROP COLUMN IF EXISTS social_handle_main")

    # Restore avatar_definitions FK
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'avatar_definitions_user_id_fkey_users'
                  AND table_name = 'avatar_definitions'
            ) THEN
                ALTER TABLE avatar_definitions DROP CONSTRAINT avatar_definitions_user_id_fkey_users;
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'avatar_definitions_user_id_fkey'
                  AND table_name = 'avatar_definitions'
            ) THEN
                ALTER TABLE avatar_definitions
                    ADD CONSTRAINT avatar_definitions_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES leads(id);
            END IF;
        END $$;
    """)

    # Reverse rename: journey_progress -> enrollments
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'journey_progress')
               AND NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'enrollments')
            THEN
                ALTER TABLE journey_progress RENAME TO enrollments;
            END IF;
        END $$;
    """)

    # Drop columns added to the renamed table (now enrollments)
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'enrollments') THEN
                ALTER TABLE enrollments DROP COLUMN IF EXISTS objection_status;
                ALTER TABLE enrollments DROP COLUMN IF EXISTS deal_value_potential;
                ALTER TABLE enrollments DROP COLUMN IF EXISTS funnel_entry_point;
                ALTER TABLE enrollments DROP COLUMN IF EXISTS product_line;
            END IF;
        END $$;
    """)
