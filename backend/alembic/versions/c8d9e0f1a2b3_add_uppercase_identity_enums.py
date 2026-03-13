"""normalize CRM enums and tenant_id to align with SQLAlchemy models

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-03-11 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c8d9e0f1a2b3'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. identitytype: Add uppercase values for messaging channels.
    # SQLAlchemy Enum columns use Python enum .name (uppercase) by default,
    # but the original migration added lowercase values for these channels.
    op.execute("ALTER TYPE identitytype ADD VALUE IF NOT EXISTS 'TELEGRAM'")
    op.execute("ALTER TYPE identitytype ADD VALUE IF NOT EXISTS 'WHATSAPP'")
    op.execute("ALTER TYPE identitytype ADD VALUE IF NOT EXISTS 'INSTAGRAM'")
    op.execute("ALTER TYPE identitytype ADD VALUE IF NOT EXISTS 'TIKTOK'")

    # 2. lifecyclestage: Add values matching Python enum names.
    # DB had STAGE_VISITOR, STAGE_LEAD, etc. but SQLAlchemy sends
    # SUBSCRIBER, LEAD, MQL, SQL, OPPORTUNITY, CUSTOMER, EVANGELIST, CHURNED.
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'SUBSCRIBER'")
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'LEAD'")
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'MQL'")
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'SQL'")
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'OPPORTUNITY'")
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'CUSTOMER'")
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'EVANGELIST'")
    op.execute("ALTER TYPE lifecyclestage ADD VALUE IF NOT EXISTS 'CHURNED'")

    # 3. Normalize tenant_id from varchar to uuid in CRM tables.
    # All other tables in the system use uuid for tenant_id.
    # The existing varchar data is already in valid UUID format.
    for table in ['customer_profiles', 'customer_identities', 'journey_events']:
        op.execute(f"""
            ALTER TABLE {table}
            ALTER COLUMN tenant_id TYPE uuid USING tenant_id::uuid
        """)


def downgrade() -> None:
    # Revert tenant_id back to varchar
    for table in ['customer_profiles', 'customer_identities', 'journey_events']:
        op.execute(f"""
            ALTER TABLE {table}
            ALTER COLUMN tenant_id TYPE character varying USING tenant_id::text
        """)
    # PostgreSQL does not support removing enum values, so we leave them.
