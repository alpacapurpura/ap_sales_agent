from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
from src.shared.domain.base_entity import Base

class ProductModel(Base):
    """
    SQLAlchemy model for Offers/Products.
    Renamed from Product to ProductModel in code, but keeps table 'products' for now.
    """
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Core Fields
    name = Column(String, nullable=False) # Maps to public_name
    type = Column(String, nullable=False)
    status = Column(String, default="DRAFT")
    internal_sku = Column(String, nullable=True)
    value_level = Column("offer_value_level", String, nullable=True) # Added for OfferValueLevel
    
    # Polymorphic Content Fields
    pricing = Column(JSONB, default=list) # List of PricingStructure
    # price_pay_in_full = Column(Float, nullable=True) # REMOVED: Not in DB
    currency = Column(String, default="USD") # Added
    dates = Column(JSONB, default=dict) # Legacy dates, kept for migration safety
    metadata_info = Column(JSONB, default=dict) # Generic metadata
    specific_details = Column(JSONB, default=dict) # The BIG JSONB for polymorphic details
    deliverables = Column(JSONB, default=list) # List of DeliverableItem
    # instructors = Column(JSONB, default=list) # REMOVED: Not in DB
    
    # Marketing & Copy
    headline_promise = Column(String, nullable=True)
    primary_outcome = Column(String, nullable=True)
    time_to_value = Column(String, nullable=True)
    marketing_pain_points = Column(JSONB, default=list)
    marketing_desires = Column(JSONB, default=list)
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
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
