from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Text, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ._base import Base

class Product(Base):
    """
    The 'Offer' Entity.
    Represents a sellable unit (Course, Mentorship, Service) with its promise and logic.
    """
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    
    # --- 1. IDENTIFICATION ---
    internal_sku = Column(String, nullable=True) # e.g., "MASTERMIND_Q1_2026"
    name = Column(String, nullable=False) # public_name
    type = Column(String, nullable=False) # Enum_Offer_Type
    delivery_model = Column(String, nullable=True) # Enum_Delivery_Model (DIY, DWY, DFY)
    status = Column(String, default="active") # Enum_Status
    
    # --- 2. THE PROMISE ---
    headline_promise = Column(String, nullable=True)
    target_avatar_match = Column(JSONB, default=[]) # List<Enum_Avatar>
    primary_outcome = Column(String, nullable=True) # The tangible result
    time_to_value = Column(String, nullable=True) # e.g. "3 weeks"
    
    # --- 3. GATEKEEPING ---
    requires_application = Column(Boolean, default=False)
    min_financial_capacity = Column(String, nullable=True) # Enum_Financial_Capacity
    prerequisites = Column(JSONB, default=[]) # List<String> of requirements
    
    # --- 4. FINANCIAL ARCHITECTURE ---
    pricing = Column(JSONB, default={}) # Stores List<Pricing_Structure>
    currency = Column(String, default="USD")
    
    # --- 5. RISK & GUARANTEE ---
    guarantee_type = Column(String, nullable=True) # Enum_Guarantee
    guarantee_terms = Column(Text, nullable=True) # Detailed legal/sales terms
    
    # --- 6. RELATIONSHIPS (Upsell/Downsell) ---
    downsell_product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    upsell_product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    includes_offers = Column(JSONB, default=[]) # List<UUID> for Value Stacking (Modular Offers)
    deliverables = Column(JSONB, default=[]) # List<Deliverable_Item> (Specifics)
    
    # --- 7. ASSETS & METADATA ---
    metadata_info = Column(JSONB, default={}) # vsl_link, checkout_url, calendar_type_id
    specific_details = Column(JSONB, default={}) # Holds polymorphic data (ProductDetails, ServiceDetails...)
    dates = Column(JSONB, default={}) # Launch dates
    
    # Avatar Override
    avatar_id = Column(UUID(as_uuid=True), ForeignKey("avatar_definitions.id"), nullable=True)
    
    # SQLAlchemy Relationships
    downsell_product = relationship("Product", remote_side=[id], foreign_keys=[downsell_product_id])
    upsell_product = relationship("Product", remote_side=[id], foreign_keys=[upsell_product_id])
    
    journeys = relationship("JourneyProgress", back_populates="product")
    avatar = relationship("AvatarDefinition", back_populates="products")

class JourneyProgress(Base):
    """
    Tracks the User's journey with a specific Product.
    Formerly 'Enrollment'.
    """
    __tablename__ = "journey_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    lead_id = Column("user_id", UUID(as_uuid=True), ForeignKey("leads.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    
    # Product Context
    product_line = Column(String, nullable=True) # Low/Mid/High Ticket
    funnel_entry_point = Column(String, nullable=True) # Ad, Webinar, Email
    deal_value_potential = Column(Float, default=0.0)

    # Status in the funnel
    status = Column(String, default="awareness")
    
    # Funnel Stage (PipelineStage Enum)
    stage = Column(String, default="NEW_LEAD")
    
    # 0-100 score based on profile match and intent
    lead_score = Column(Integer, default=0)
    
    # Objections raised
    objection_status = Column(String, nullable=True) # Current blocker
    objections = Column(JSONB, default=[]) # History (legacy/detail)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    lead = relationship("Lead", back_populates="journeys")
    product = relationship("Product", back_populates="journeys")

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    lead_id = Column("user_id", UUID(as_uuid=True), ForeignKey("leads.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default="scheduled") # scheduled, completed, no_show, cancelled
    meeting_link = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lead = relationship("Lead", back_populates="appointments")

class AvatarDefinition(Base):
    """
    Global Avatar Configuration (ICP & Anti-Avatar).
    Now supports Multi-Instance (Global vs Niche).
    """
    __tablename__ = "avatar_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    # Removed unique=True to allow multiple avatars
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id")) 
    
    name = Column(String, nullable=False, default="Avatar General")
    is_default = Column(Boolean, default=False)
    scope = Column(String, default="GLOBAL") # GLOBAL, OFFER_SPECIFIC
    
    icp_description = Column(Text, nullable=True) # Ideal Customer Profile
    anti_avatar = Column(Text, nullable=True) # Who NOT to sell to
    voice_tone_config = Column(JSONB, default={}) # Personality settings
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User")
    products = relationship("Product", back_populates="avatar")

class MarketingAsset(Base):
    """
    Content Assets (Webinars, VSLs, PDFs) that feed the context.
    """
    __tablename__ = "marketing_assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True) # Can be global if null
    
    name = Column(String, nullable=False)
    type = Column(String, nullable=False) # webinar, vsl, pdf, landing
    url = Column(String, nullable=True)
    transcript_summary = Column(Text, nullable=True)
    hook_points = Column(JSONB, default=[])
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")
    documents = relationship("Document", back_populates="marketing_asset")

class Objection(Base):
    """
    Structured Objection Matrix for training.
    """
    __tablename__ = "objections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    
    trigger_phrase = Column(String, nullable=False) # "Es muy caro"
    rebuttal_strategy = Column(Text, nullable=True) # "Value Stack"
    script = Column(Text, nullable=True) # "Comparado con..."
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product")

class OfferLog(Base):
    """
    Tracks specific pitch events (When was a product offered?)
    """
    __tablename__ = "offer_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    lead_id = Column("user_id", UUID(as_uuid=True), ForeignKey("leads.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    
    offered_at = Column(DateTime(timezone=True), server_default=func.now())
    pitch_type = Column(String) # e.g., "webinar_invite", "program_pitch", "downsell"
    response = Column(String, default="pending") # pending, accepted, rejected, ignored
    
    lead = relationship("Lead")
    product = relationship("Product")

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    filename = Column(String, nullable=False)
    collection_name = Column(String, nullable=False)
    category = Column(String, default="general") # factural, style, objection, general
    chunk_count = Column(Integer, default=0)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="indexed") # indexed, error
    
    # Metadata extra (e.g. description, author)
    metadata_info = Column(JSONB, default={})

    # Multi-scoped Context
    scope = Column(String, default="GLOBAL") # GLOBAL, OFFER, ASSET
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    marketing_asset_id = Column(UUID(as_uuid=True), ForeignKey("marketing_assets.id"), nullable=True)

    # Relationships
    product = relationship("Product")
    marketing_asset = relationship("MarketingAsset", back_populates="documents")

class PromptVersion(Base):
    """
    Manages versions of Prompt Templates.
    Enables runtime updates and audit trail for prompts.
    """
    __tablename__ = "prompt_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    key = Column(String, nullable=False, index=True) # e.g., "sales_system"
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False) # Jinja2 template content
    is_active = Column(Boolean, default=False)
    
    change_reason = Column(String, nullable=False) # Mandatory audit field
    author_id = Column(String, default="admin") # User who made the change
    
    metadata_info = Column(JSONB, default={})
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SensitiveData(Base):
    """
    Registry of sensitive data patterns and replacement rules.
    Used by the Safety Layer to sanitize outputs.
    """
    __tablename__ = "sensitive_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    pattern = Column(String, nullable=False) # Regex or Keyword
    replacement = Column(String, nullable=False) # e.g. [REDACTED]
    category = Column(String, nullable=False) # financial, pii, business_secret, system
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Advanced: LLM Instructions for context-aware replacement
    context_instruction = Column(Text, nullable=True) 
    
    # Scope Configuration
    scope = Column(String, default="BRAND") # BRAND, PRODUCT
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product")
