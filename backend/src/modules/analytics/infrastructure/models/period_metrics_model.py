"""Period metrics table — deduplicated metrics for multi-day periods.

Stores NON_AGGREGABLE metrics (reach, users, frequency) that are extracted
directly from APIs at weekly/monthly/quarterly granularity, avoiding the
inaccurate daily-SUM approach.
"""

import uuid

from sqlalchemy import Column, Date, DateTime, Float, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class PeriodMetricModel(Base):
    __tablename__ = "period_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String, nullable=False)
    channel_slug = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    currency = Column(String, nullable=True)

    period_type = Column(String, nullable=False)  # weekly, monthly, quarterly
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Ad-level dimensions
    campaign_id = Column(String, nullable=True)
    ad_set_id = Column(String, nullable=True)
    ad_id = Column(String, nullable=True)

    cost_type = Column(String, nullable=True)
    extra = Column(JSONB, server_default="{}")
    source_extraction_run_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
