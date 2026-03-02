from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
import uuid
from src.shared.domain.base_entity import Base
from src.modules.assets.domain.enums import AssetType, StorageProvider, AssetStatus

class AssetModel(Base):
    """
    Generic Asset storage for Tenants.
    Renamed from GalleryImageModel to AssetModel.
    Table: assets (renamed from offer_gallery_images)
    """
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    
    # Optional Link to Offer (Backward Compatibility & Offer Context)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True, index=True)
    
    # Asset Details
    type = Column(String, default=AssetType.IMAGE.value) # Enum as String for DB compatibility
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    
    # Storage Info
    storage_provider = Column(String, default=StorageProvider.LOCAL.value)
    storage_path = Column(String, nullable=True) # Internal path/key
    public_url = Column(String, nullable=False) # Accessible URL
    
    # Metadata & AI
    user_description = Column(Text, nullable=True)
    ai_metadata = Column(JSONB, default={}) # Consolidated AI analysis
    
    # Legacy Columns (kept for backward compatibility, mapped to ai_metadata logic in service)
    ai_description = Column(Text, nullable=True)
    ai_colors = Column(JSONB, default=[])

    # Status
    status = Column(String, default=AssetStatus.PROCESSING.value)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
