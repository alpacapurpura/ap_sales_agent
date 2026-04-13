"""SQLAlchemy model for ad_sets table."""

import uuid

from sqlalchemy import BigInteger, Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class AdSetModel(Base):
    """SQLAlchemy model for ad set."""

    __tablename__ = "ad_sets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String(50), nullable=False, default="meta")
    external_id = Column(String(255), nullable=False)
    campaign_external_id = Column(String(255), nullable=False)
    name = Column(String(500), nullable=False)
    status = Column(String(50))
    effective_status = Column(String(50))
    optimization_goal = Column(String(100))
    billing_event = Column(String(100))
    bid_strategy = Column(String(100))
    daily_budget = Column(BigInteger)
    lifetime_budget = Column(BigInteger)
    budget_remaining = Column(BigInteger)
    targeting = Column(JSONB, server_default="{}")
    destination_type = Column(String(100))
    learning_stage = Column(String(50))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    extra = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
