"""SQLAlchemy model for ad_campaign_templates.

Read-only seed data consumed by CampaignTemplateService. These templates
are the base for the future Action Trigger that will create Meta campaigns
programmatically.
"""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class AdCampaignTemplateModel(Base):
    """Suggested Meta campaign configuration keyed by offer archetype."""

    __tablename__ = "ad_campaign_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    offer_archetype = Column(String(50), nullable=False)
    offer_onboarding_action = Column(String(50), nullable=True)
    offer_is_lead_magnet = Column(Boolean, nullable=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    recommended_objective = Column(String(50), nullable=False)
    recommended_optimization_goal = Column(String(100))
    recommended_destination_type = Column(String(100))
    structure_hints = Column(JSONB, server_default="{}")
    priority = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
