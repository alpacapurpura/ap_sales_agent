"""SQLAlchemy model for appointment model."""

import uuid

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class AppointmentModel(Base):
    """SQLAlchemy model for appointment."""

    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    lead_id = Column(
        UUID(as_uuid=True),
        ForeignKey("leads.id"),
        nullable=True,
        index=True,
    )

    summary = Column(String, nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    status = Column(
        String,
        default="SCHEDULED",
    )  # SCHEDULED, CANCELLED, COMPLETED, NO_SHOW
    meeting_link = Column(String, nullable=True)

    external_event_id = Column(String, nullable=True)  # Google Calendar ID
    metadata_info = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    lead = relationship("LeadModel", back_populates="appointments")
