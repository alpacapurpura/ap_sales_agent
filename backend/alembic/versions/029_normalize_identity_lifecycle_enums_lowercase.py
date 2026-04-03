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
from sqlalchemy import text

revision = "029_normalize_enums_lowercase"
down_revision = "028_fix_appointments_tenant_id"
branch_labels = None
depends_on = None


def _add_enum_value_if_missing(conn, enum_type: str, label: str) -> None:
    """Add a label to a PostgreSQL enum if it does not already exist.

    ALTER TYPE … ADD VALUE must be executed outside a transaction block
    (PostgreSQL restriction).  We detect whether the label exists first and
    only issue the DDL when it is truly missing, so the statement is safe to
    call repeatedly (idempotent).
    """
    exists = conn.execute(
        text(
            "SELECT 1 FROM pg_enum "
            "WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = :etype) "
            "AND enumlabel = :label"
        ),
        {"etype": enum_type, "label": label},
    ).scalar()
    if not exists:
        # Execute outside the current transaction so the new value is
        # immediately visible to subsequent DML in the same migration.
        conn.execute(
            text(
                f"ALTER TYPE {enum_type} ADD VALUE '{label}'"
            ).execution_options(autocommit=True)
        )


def upgrade() -> None:
    bind = op.get_bind()

    # -- 0. Ensure lowercase identitytype labels exist (idempotent) -------------
    for label in ("email", "phone", "cookie_id", "user_id", "device_id",
                  "social_handle", "external_id"):
        _add_enum_value_if_missing(bind, "identitytype", label)

    # -- 0b. Ensure lowercase lifecyclestage labels exist (idempotent) ----------
    for label in ("subscriber", "lead", "mql", "sql", "opportunity",
                  "customer", "evangelist", "churned"):
        _add_enum_value_if_missing(bind, "lifecyclestage", label)

    # -- 1. Normalise customer_identities.type: uppercase -> lowercase ----------
    op.execute("""
        UPDATE customer_identities
        SET type = lower(type::text)::identitytype
        WHERE type::text <> lower(type::text);
    """)

    # -- 2. Normalise customer_profiles.lifecycle_stage ------------------------
    op.execute("""
        UPDATE customer_profiles
        SET lifecycle_stage = lower(lifecycle_stage::text)::lifecyclestage
        WHERE lifecycle_stage IS NOT NULL
          AND lifecycle_stage::text <> lower(lifecycle_stage::text);
    """)

    # -- 3. Normalise lifecycle_transitions.from_stage / to_stage --------------
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
