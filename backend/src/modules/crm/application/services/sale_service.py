from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from src.modules.crm.domain.sale import Sale
from src.modules.crm.domain.enums import SaleStatus, SaleStage, PaymentMethod
from src.modules.crm.infrastructure.repositories.sale_repository import SaleRepository

class SaleService:
    def __init__(self, db: Session):
        self.repository = SaleRepository(db)

    def create_sale(self, 
        tenant_id: UUID,
        customer_id: UUID,
        offer_id: UUID,
        amount: float,
        payment_method: PaymentMethod,
        transaction_id: Optional[str] = None,
        source: str = "MANUAL",
        metadata: Optional[dict] = None,
        status: SaleStatus = SaleStatus.COMPLETED
    ) -> Sale:
        # Determine Stage logic: 
        # If the customer has 0 COMPLETED sales, this is CONVERSION (Acquisition).
        # If they have > 0, it is EXPANSION (Retention/Upsell).
        previous_sales_count = self.repository.count_sales_by_customer(customer_id)
        stage = SaleStage.CONVERSION if previous_sales_count == 0 else SaleStage.EXPANSION
        
        sale = Sale(
            id=uuid4(),
            tenant_id=tenant_id,
            customer_id=customer_id,
            offer_id=offer_id,
            transaction_id=transaction_id,
            amount=amount,
            currency="USD",
            status=status,
            stage=stage,
            source=source,
            payment_method=payment_method,
            metadata=metadata or {},
            occurred_at=datetime.now()
        )
        
        return self.repository.save(sale)
