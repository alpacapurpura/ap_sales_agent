"""Normalize identitytype and lifecyclestage enum values to lowercase.

The Python enums IdentityType and LifecycleStage define lowercase .value
(e.g., "email", "subscriber"), but SQLAlchemy was previously configured to
store .name (uppercase, e.g., "EMAIL", "SUBSCRIBER"). This migration
normalises any existing uppercase rows to lowercase, matching the
PostgreSQL enum labels created in the original migration (194925304af0).

Revision ID: 029_normalize_enums_lowercase
Revises: 028_fix_appointments_tenant_id
"""

from alembic import op

revision = "029_normalize_enums_lowercase"
down_revision = "028_fix_appointments_tenant_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- 1. Normalise customer_identities.type: uppercase -> lowercase ---------
    # Cast to text, lowercase, cast back to the enum.
    # Only touch rows that have an uppercase value (safe no-op otherwise).
    op.execute("""
        UPDATE customer_identities
        SET type = lower(type::text)::identitytype
        WHERE type::text <> lower(type::text);
    """)

    # -- 2. Normalise customer_profiles.lifecycle_stage -------------------------
    op.execute("""
        UPDATE customer_profiles
        SET lifecycle_stage = lower(lifecycle_stage::text)::lifecyclestage
        WHERE lifecycle_stage IS NOT NULL
          AND lifecycle_stage::text <> lower(lifecycle_stage::text);
    """)

    # -- 3. Normalise lifecycle_transitions.from_stage / to_stage ---------------
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'lifecycle_transitions'
            ) THEN
                UPDATE lifecycle_transitions
                SET from_stage = lower(from_stage::text)::lifecyclestage
                WHERE from_stage IS NOT NULL
                  AND from_stage::text <> lower(from_stage::text);

                UPDATE lifecycle_transitions
                SET to_stage = lower(to_stage::text)::lifecyclestage
                WHERE to_stage::text <> lower(to_stage::text);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Lowercase values are the canonical form; no rollback needed.
    pass
