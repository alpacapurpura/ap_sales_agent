"""Official metrics table — validated, deduplicated data for dashboards."""

import uuid

from sqlalchemy import Column, Date, DateTime, Float, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base
from src.shared.infrastructure.database.types import EncryptedJSON


class OfficialMetricModel(Base):
    __tablename__ = "official_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String, nullable=False)
    channel_slug = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    currency = Column(String, nullable=True)
    metric_date = Column(Date, nullable=False, index=True)

    # Monetary values encrypted at rest
    spend = Column(EncryptedJSON, nullable=True)
    revenue = Column(EncryptedJSON, nullable=True)

    # Ad-level dimensions
    campaign_id = Column(String, nullable=True)
    ad_set_id = Column(String, nullable=True)
    ad_id = Column(String, nullable=True)

    # CostType enum value (neutral, expense, investment, revenue)
    cost_type = Column(String, nullable=True)

    extra = Column(JSONB, server_default="{}")
    source_extraction_run_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index(
            "ix_official_tenant_channel_date",
            "tenant_id",
            "channel_slug",
            "metric_date",
        ),
    )
