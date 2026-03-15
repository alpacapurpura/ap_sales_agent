"""Metric aggregation table — pre-computed rollups for dashboard performance."""

import uuid

from sqlalchemy import Column, Date, DateTime, Float, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class MetricAggregationModel(Base):
    __tablename__ = "metric_aggregations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    channel_slug = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    period_type = Column(String, nullable=False)  # daily, weekly, monthly, last_30_days
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    currency = Column(String, nullable=True)
    cost_type = Column(String, nullable=True)

    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    extraction_run_id = Column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        Index(
            "ix_agg_tenant_channel_period",
            "tenant_id",
            "channel_slug",
            "period_type",
            "period_start",
        ),
    )
