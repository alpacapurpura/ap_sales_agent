"""Channel cost settings model for per-tenant cost configuration.

Business owners configure monthly costs per channel from Growth Studio settings.
Supports multiple cost entries per channel (platform, agency, tool, llm).
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class ChannelCostSettingModel(Base):
    __tablename__ = "channel_cost_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    channel_slug = Column(
        String,
        nullable=False,
    )  # "mailerlite", "whatsapp-inbound", etc.
    cost_type = Column(String, nullable=False)  # "platform", "agency", "tool", "llm"
    monthly_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    proration_category = Column(
        String,
        nullable=True,
    )  # "organic_management", "paid_management", "video", "full_service"
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # soft delete

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "channel_slug",
            "cost_type",
            name="uq_channel_cost_tenant_slug_type",
        ),
    )
