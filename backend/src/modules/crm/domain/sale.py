from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import Field
from src.shared.domain.base_entity import BaseEntity
from src.modules.crm.domain.enums import SaleStatus, SaleStage, PaymentMethod

class Sale(BaseEntity):
    id: UUID
    tenant_id: UUID
    customer_id: UUID
    offer_id: UUID
    transaction_id: Optional[str] = None
    
    amount: float
    currency: str = "USD"
    
    status: SaleStatus
    stage: SaleStage
    
    source: str = "MANUAL" # SHOPIFY, STRIPE, API
    payment_method: Optional[PaymentMethod] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
