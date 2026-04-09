from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from src.modules.crm.domain.enums import PaymentMethod, SaleStage, SaleStatus
from src.shared.domain.base_entity import BaseEntity


class Sale(BaseEntity):
    id: UUID
    tenant_id: UUID
    customer_id: UUID
    offer_id: UUID
    transaction_id: str | None = None

    amount: float
    currency: str

    status: SaleStatus
    stage: SaleStage

    source: str = "MANUAL"  # SHOPIFY, STRIPE, API
    payment_method: PaymentMethod | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime

    created_at: datetime | None = None
    updated_at: datetime | None = None
