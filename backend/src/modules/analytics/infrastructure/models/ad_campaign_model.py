"""SQLAlchemy model for ad_campaigns table."""

import uuid

from sqlalchemy import BigInteger, Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class AdCampaignModel(Base):
    """SQLAlchemy model for ad campaign."""

    __tablename__ = "ad_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String(50), nullable=False, default="meta")
    external_id = Column(String(255), nullable=False)
    name = Column(String(500), nullable=False)
    objective = Column(String(100))
    status = Column(String(50))
    effective_status = Column(String(50))
    bid_strategy = Column(String(100))
    daily_budget = Column(BigInteger)
    lifetime_budget = Column(BigInteger)
    budget_remaining = Column(BigInteger)
    buying_type = Column(String(50), default="AUCTION")
    special_ad_categories = Column(JSONB, server_default="[]")
    start_time = Column(DateTime(timezone=True))
    stop_time = Column(DateTime(timezone=True))
    external_created_time = Column(DateTime(timezone=True))
    external_updated_time = Column(DateTime(timezone=True))
    extra = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
