"""add_etl_infrastructure_tables_and_tenant_priority

Revision ID: ab8346fd2c09
Revises: f5a6b7c8d9e0
Create Date: 2026-03-15 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ab8346fd2c09"
down_revision: Union[str, None] = "f5a6b7c8d9e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- extraction_runs (must be created first — referenced by staging_metrics FK) ---
    op.create_table(
        "extraction_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("metrics_count", sa.Integer(), server_default="0"),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("rows_extracted", sa.Integer(), server_default="0"),
        sa.Column("rate_limit_headroom", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_extraction_runs_tenant_id", "extraction_runs", ["tenant_id"])
    op.create_index(
        "ix_extraction_tenant_provider_status",
        "extraction_runs",
        ["tenant_id", "provider", "status"],
    )

    # --- staging_metrics ---
    op.create_table(
        "staging_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("channel_slug", sa.String(), nullable=False),
        sa.Column("metric_name", sa.String(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("spend", postgresql.JSONB(), nullable=True),
        sa.Column("revenue", postgresql.JSONB(), nullable=True),
        sa.Column("campaign_id", sa.String(), nullable=True),
        sa.Column("ad_set_id", sa.String(), nullable=True),
        sa.Column("ad_id", sa.String(), nullable=True),
        sa.Column("extra", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "extraction_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("extraction_runs.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_staging_metrics_tenant_id", "staging_metrics", ["tenant_id"])
    op.create_index("ix_staging_metrics_provider", "staging_metrics", ["provider"])
    op.create_index(
        "ix_staging_metrics_metric_date", "staging_metrics", ["metric_date"]
    )
    op.create_index(
        "ix_staging_tenant_provider_date",
        "staging_metrics",
        ["tenant_id", "provider", "metric_date"],
    )

    # --- official_metrics ---
    op.create_table(
        "official_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("channel_slug", sa.String(), nullable=False),
        sa.Column("metric_name", sa.String(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("metric_date", sa.Date(), nullable=False),
        sa.Column("spend", postgresql.JSONB(), nullable=True),
        sa.Column("revenue", postgresql.JSONB(), nullable=True),
        sa.Column("campaign_id", sa.String(), nullable=True),
        sa.Column("ad_set_id", sa.String(), nullable=True),
        sa.Column("ad_id", sa.String(), nullable=True),
        sa.Column("cost_type", sa.String(), nullable=True),
        sa.Column("extra", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "source_extraction_run_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_official_metrics_tenant_id", "official_metrics", ["tenant_id"]
    )
    op.create_index(
        "ix_official_metrics_metric_date", "official_metrics", ["metric_date"]
    )
    op.create_index(
        "ix_official_tenant_channel_date",
        "official_metrics",
        ["tenant_id", "channel_slug", "metric_date"],
    )

    # --- metric_aggregations ---
    op.create_table(
        "metric_aggregations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel_slug", sa.String(), nullable=False),
        sa.Column("metric_name", sa.String(), nullable=False),
        sa.Column("period_type", sa.String(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("cost_type", sa.String(), nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "extraction_run_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
    )
    op.create_index(
        "ix_metric_aggregations_tenant_id", "metric_aggregations", ["tenant_id"]
    )
    op.create_index(
        "ix_agg_tenant_channel_period",
        "metric_aggregations",
        ["tenant_id", "channel_slug", "period_type", "period_start"],
    )

    # --- Add extraction_priority to tenants ---
    op.add_column(
        "tenants",
        sa.Column(
            "extraction_priority",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "extraction_priority")
    op.drop_table("metric_aggregations")
    op.drop_table("official_metrics")
    op.drop_table("staging_metrics")
    op.drop_table("extraction_runs")
