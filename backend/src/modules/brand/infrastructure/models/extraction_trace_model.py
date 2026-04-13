import uuid

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class BrandExtractionTrace(Base):
    __tablename__ = "brand_extraction_traces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    job_id = Column(String, nullable=False, index=True)

    # Config
    mode = Column(String, nullable=False)  # "initial" | "update"
    profile_name = Column(String, nullable=False)  # "safe" | "fast"
    url = Column(Text, nullable=True)
    include_visuals = Column(String, default="false")
    include_assets = Column(String, default="false")

    # Results
    status = Column(
        String,
        nullable=False,
        default="running",
    )  # running | completed | failed
    content_length = Column(Integer, default=0)
    sections_total = Column(Integer, default=0)
    sections_succeeded = Column(Integer, default=0)
    total_duration_s = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timeline of events: [{event, section, ts, duration_s, meta}]
    events = Column(JSONB, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
