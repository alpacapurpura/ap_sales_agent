"""Add lead_id to appointments table.

Revision ID: 030_add_lead_id_to_appointments
Revises: 029_normalize_enums_lowercase
"""

revision = "030_add_lead_id_to_appointments"
down_revision = "029_normalize_enums_lowercase"

from alembic import op


def upgrade() -> None:
    op.execute(
        "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS lead_id UUID REFERENCES leads(id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_appointments_lead_id ON appointments (lead_id);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_appointments_lead_id;")
    op.execute("ALTER TABLE appointments DROP COLUMN IF EXISTS lead_id;")
