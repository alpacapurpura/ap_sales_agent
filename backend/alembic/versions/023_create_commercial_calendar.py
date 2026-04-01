"""Create commercial_calendar_events table.

Revision ID: 023_commercial_calendar
Revises: 022_value_levels
"""
from alembic import op

revision = "023_commercial_calendar"
down_revision = "022_value_levels"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS commercial_calendar_events (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID,
            country_code VARCHAR(2)   NOT NULL,
            date        DATE          NOT NULL,
            year        INTEGER       NOT NULL,
            week_number INTEGER       NOT NULL,
            name        VARCHAR(255)  NOT NULL,
            category    VARCHAR(100),
            description TEXT,
            created_at  TIMESTAMPTZ   NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS ix_cal_country ON commercial_calendar_events (country_code)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cal_year    ON commercial_calendar_events (year)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cal_week    ON commercial_calendar_events (week_number)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cal_tenant  ON commercial_calendar_events (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cal_cc_year_date ON commercial_calendar_events (country_code, year, date)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS commercial_calendar_events")
