"""Product SQLAlchemy model."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class ProductModel(Base):
    """SQLAlchemy model for Offers/Products.

    Renamed from Product to ProductModel in code, but keeps table 'products' for now.
    """

    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)

    # Core Fields
    name = Column(String, nullable=False)  # Maps to public_name
    status = Column(String, default="draft")
    internal_sku = Column(String, nullable=True)
    value_level = Column("offer_value_level", String, nullable=True)

    # Archetype system
    archetype = Column(String, nullable=False)
    format_hint = Column(String, nullable=True)
    is_lead_magnet = Column(Boolean, default=False, server_default="false")
    has_editions = Column(Boolean, nullable=False, default=True, server_default="true")

    # OfferTypePreset (Sprint 12 — 7th SSoT axis). Optional link to a preset
    # in ``offer_type_preset_catalog.py``. Nullable for legacy rows and for
    # offers created before the wizard rehauled the picker flow. Indexed on
    # (tenant_id, preset_id) to support analytics segmentation + agent
    # grounding queries.
    preset_id = Column(String, nullable=True, index=True)

    # Polymorphic Content Fields
    pricing = Column(JSONB, default=list)  # List of PricingStructure
    # Nullable: resolved to TenantLocale.currency by the application layer.
    currency = Column(String, nullable=True)

    # --- Pricing LATAM (Fase 01 — migration 062) ---
    tax_included = Column(Boolean, nullable=True)
    installments_available = Column(Text, nullable=True)
    accepted_payment_providers = Column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )
    dates = Column(JSONB, default=dict)  # Legacy dates, kept for migration safety
    metadata_info = Column(JSONB, default=dict)  # Generic metadata
    specific_details = Column(
        JSONB,
        default=dict,
    )  # The BIG JSONB for polymorphic details
    deliverables = Column(JSONB, default=list)  # List of DeliverableItem

    # Marketing & Copy
    headline_promise = Column(String, nullable=True)
    primary_outcome = Column(String, nullable=True)
    time_to_value = Column(String, nullable=True)
    marketing_pain_points = Column(JSONB, default=list)
    marketing_desires = Column(JSONB, default=list)
    objections = Column(JSONB, default=list)
    target_avatar_match = Column(JSONB, default=list)

    # Access & Duration
    access_duration = Column(String, nullable=True)
    access_duration_text = Column(String, nullable=True)
    support_duration_days = Column(Integer, nullable=True)
    delivery_model = Column(String, nullable=True)

    # Gatekeeping & Sales Logic
    requires_application = Column(Boolean, default=False)
    min_financial_capacity = Column(String, nullable=True)
    prerequisites = Column(JSONB, default=list)
    anti_avatar_keywords = Column(JSONB, default=list)

    # Guarantee
    guarantee_type = Column(String, nullable=True)
    guarantee_terms = Column(Text, nullable=True)

    # Relationships / Upsells
    downsell_product_id = Column(UUID(as_uuid=True), nullable=True)
    upsell_product_id = Column(UUID(as_uuid=True), nullable=True)
    includes_offers = Column(JSONB, default=list)
    avatar_id = Column(UUID(as_uuid=True), nullable=True)

    # Onboarding & Funnel
    onboarding_action = Column(String, nullable=True)
    onboarding_url = Column(String, nullable=True)
    calendar_type_id = Column(String, nullable=True)
    checkout_page_url = Column(String, nullable=True)
    vsl_link = Column(String, nullable=True)
    landing_page_config = Column(JSONB, default=dict)

    # Extra fields from Domain Offer not explicitly in old model (mapped to columns or JSON?)
    # price_pay_in_full -> could be stored in pricing list or separate column if needed.
    # For now, we'll assume it might be extracted from pricing list or added if critical.
    # currency -> stored in pricing objects usually, or add column.

    # --- Narrative: promise ----------------------------------------------
    before_state = Column(Text, nullable=True)
    after_state = Column(Text, nullable=True)
    why_now = Column(Text, nullable=True)
    measurable_outcomes = Column(JSONB, nullable=False, default=list, server_default="[]")

    # --- Narrative: psychology -------------------------------------------
    cultural_trust_barriers = Column(JSONB, nullable=False, default=list, server_default="[]")
    emotional_triggers = Column(JSONB, nullable=False, default=list, server_default="[]")
    status_drivers = Column(JSONB, nullable=False, default=list, server_default="[]")
    regret_scenarios = Column(JSONB, nullable=False, default=list, server_default="[]")

    # --- Narrative: closing ----------------------------------------------
    refund_process_description = Column(Text, nullable=True)
    urgency_drivers = Column(JSONB, nullable=False, default=list, server_default="[]")
    scarcity_reason_honest = Column(Text, nullable=True)
    bonus_if_act_now = Column(Text, nullable=True)
    final_push_copy = Column(Text, nullable=True)

    # Lifecycle (SaaS archive + soft-delete)
    # archived_at NULL, deleted_at NULL -> active (visible in normal list)
    # archived_at NOT NULL, deleted_at NULL -> archived (visible in /archived)
    # deleted_at NOT NULL -> soft-deleted (hidden everywhere)
    archived_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
