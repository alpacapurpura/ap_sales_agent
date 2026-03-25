"""add unique index for official_metrics upsert

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-25 22:45:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_official_metrics_natural_key
        ON official_metrics (tenant_id, provider, channel_slug, metric_name, metric_date)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_official_metrics_natural_key")
