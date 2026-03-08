from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from src.shared.domain.base_entity import Base
from src.modules.crm.domain.enums import SaleStatus, SaleStage, PaymentMethod

class SaleModel(Base):
    __tablename__ = "sales"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customer_profiles.id"), nullable=False, index=True)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    
    transaction_id = Column(String, nullable=True, index=True)
    
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    
    status = Column(Enum(SaleStatus), default=SaleStatus.PENDING)
    stage = Column(Enum(SaleStage), nullable=False)
    
    source = Column(String, default="MANUAL")
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    
    metadata_info = Column(JSONB, default=dict)
    occurred_at = Column(DateTime(timezone=True), default=func.now())
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer = relationship("src.modules.crm.infrastructure.models.customer_model.CustomerProfileModel", backref="sales")
    offer = relationship("src.modules.offer.infrastructure.models.product_model.ProductModel")
