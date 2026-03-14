"""normalize CRM enums and tenant_id to align with SQLAlchemy models

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-03-11 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = 'c8d9e0f1a2b3'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. identitytype: Add uppercase values for messaging channels.
    op.execute("ALTER TYPE identitytype ADD VALUE IF NOT EXISTS 'TELEGRAM'")
    op.execute("ALTER TYPE identitytype ADD VALUE IF NOT EXISTS 'WHATSAPP'")
    op.execute("ALTER TYPE identitytype ADD VALUE IF NOT EXISTS 'INSTAGRAM'")
    op.execute("ALTER TYPE identitytype ADD VALUE IF NOT EXISTS 'TIKTOK'")

    # 2. lifecyclestage: Add values matching Python enum names.
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'SUBSCRIBER'")
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'LEAD'")
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'MQL'")
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'SQL'")
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'OPPORTUNITY'")
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'CUSTOMER'")
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'EVANGELIST'")
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'CHURNED'")

    # 3. Normalize tenant_id from varchar to uuid in CRM tables (only if table/column exists).
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    for table in ['customer_profiles', 'customer_identities', 'journey_events']:
        if table not in existing_tables:
            print(f"Skipping type conversion for {table} - table does not exist")
            continue

        columns = {c['name']: c for c in inspector.get_columns(table)}
        if 'tenant_id' not in columns:
            print(f"Skipping type conversion for {table} - tenant_id column missing")
            continue

        col_type = str(columns['tenant_id']['type'])
        if 'UUID' in col_type.upper():
            print(f"Skipping type conversion for {table} - tenant_id already UUID")
            continue

        op.execute(f"""
            ALTER TABLE {table}
            ALTER COLUMN tenant_id TYPE uuid USING tenant_id::uuid
        """)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    for table in ['customer_profiles', 'customer_identities', 'journey_events']:
        if table not in existing_tables:
            continue
        op.execute(f"""
            ALTER TABLE {table}
            ALTER COLUMN tenant_id TYPE character varying USING tenant_id::text
        """)
    # PostgreSQL does not support removing enum values, so we leave them.
