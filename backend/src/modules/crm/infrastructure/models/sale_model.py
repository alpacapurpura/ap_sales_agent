import uuid

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.modules.crm.domain.enums import PaymentMethod, SaleStage, SaleStatus
from src.shared.domain.base_entity import Base


class SaleModel(Base):
    __tablename__ = "sales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_profiles.id"),
        nullable=False,
        index=True,
    )
    offer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False,
        index=True,
    )

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
    customer = relationship("CustomerProfileModel", backref="sales")
    offer = relationship("ProductModel")
