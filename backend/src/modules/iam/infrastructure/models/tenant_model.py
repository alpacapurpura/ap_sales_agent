"""SQLAlchemy model for tenant model."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base
from src.shared.domain.currency import FALLBACK_CURRENCY


class TenantModel(Base):
    """SQLAlchemy model for tenant."""

    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)  # For subdomain/lookup
    # Configuration for Prompts and Rules
    # Configuration for Prompts and Rules
    # e.g. { "company_name": "Visionarias" }
    config_json = Column(JSONB, default={})
    default_currency = Column(String, server_default=FALLBACK_CURRENCY)
    timezone = Column(String, server_default="UTC")

    # ETL extraction priority: higher value = extracted first (premium tenants)
    extraction_priority = Column(Integer, server_default="0", nullable=False)

    # AI Provider Configuration (Multitenant).
    # T-6c (PI-12 S1, alembic 124_drop_tenant_provider_api_keys) physically
    # dropped 4 deprecated per-tenant provider API key columns. gemini_api_key
    # remains active per architect §2.4 (Q4 ratification) because landing
    # extractors still call Gemini directly bypassing the LiteLLM Proxy.
    gemini_api_key = Column(String, nullable=True)
    webhook_secret = Column(String, nullable=True)
    can_use_platform_keys = Column(Boolean, default=False)

    tracking_config = Column(JSONB, default={}, nullable=True)

    # Period configuration for ETL aggregation
    weekly_start_day = Column(Integer, server_default="0")  # 0=Mon, 6=Sun
    fiscal_year_start_month = Column(Integer, server_default="1")  # January
    fiscal_year_start_day = Column(Integer, server_default="1")

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship(
        "UserModel",
        secondary="user_tenants",
        back_populates="tenants",
    )
    leads = relationship("LeadModel", back_populates="tenant")
