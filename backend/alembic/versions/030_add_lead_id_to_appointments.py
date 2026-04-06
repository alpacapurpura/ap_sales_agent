"""Add lead_id to appointments table.

Revision ID: 030_add_lead_id_to_appointments
Revises: 029_normalize_enums_lowercase
"""

from alembic import op

revision = "030_add_lead_id_to_appointments"
down_revision = "029_normalize_enums_lowercase"


def upgrade() -> None:
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'appointments'
            ) THEN
                ALTER TABLE appointments
                ADD COLUMN IF NOT EXISTS lead_id UUID REFERENCES leads(id);

                CREATE INDEX IF NOT EXISTS ix_appointments_lead_id
                ON appointments (lead_id);
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_appointments_lead_id;")
    op.execute("ALTER TABLE appointments DROP COLUMN IF EXISTS lead_id;")
