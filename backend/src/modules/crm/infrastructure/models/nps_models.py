"""NPS survey and response models for Net Promoter Score tracking."""
import uuid

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class NpsSurveyModel(Base):
    __tablename__ = "nps_surveys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    token = Column(String, nullable=False, unique=True, index=True)
    offer_id = Column(UUID(as_uuid=True), nullable=True)  # null = individual survey
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_profiles.id"),
        nullable=True,
    )
    delivery_channel = Column(String, default="universal_link")  # "universal_link" | "whatsapp"
    status = Column(String, default="pending")  # "pending" | "sent" | "responded" | "expired"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_nps_surveys_tenant_customer", "tenant_id", "customer_id"),
    )


class NpsResponseModel(Base):
    __tablename__ = "nps_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    survey_id = Column(
        UUID(as_uuid=True),
        ForeignKey("nps_surveys.id"),
        nullable=False,
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_profiles.id"),
        nullable=False,
        index=True,
    )
    score = Column(Integer, nullable=False)  # 0-10
    feedback_text = Column(String, nullable=True)
    testimonial_text = Column(String, nullable=True)
    testimonial_audio_url = Column(String, nullable=True)
    consent_public_use = Column(Boolean, default=False)
    responded_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_nps_responses_tenant_survey", "tenant_id", "survey_id"),
    )
