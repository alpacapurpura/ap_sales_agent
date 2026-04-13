from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.modules.crm.domain.enums import PaymentMethod, SaleStage, SaleStatus
from src.modules.crm.domain.events import SaleCompletedEvent
from src.modules.crm.domain.sale import Sale
from src.modules.crm.infrastructure.repositories.sale_repository import SaleRepository
from src.shared.domain.events import EventBus


class SaleService:
    def __init__(self, db: Session):
        self.repository = SaleRepository(db)

    def create_sale(
        self,
        tenant_id: UUID,
        customer_id: UUID,
        offer_id: UUID,
        amount: float,
        payment_method: PaymentMethod,
        transaction_id: str | None = None,
        source: str = "MANUAL",
        metadata: dict | None = None,
        status: SaleStatus = SaleStatus.COMPLETED,
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
            occurred_at=datetime.now(UTC),
        )

        saved_sale = self.repository.save(sale)

        # Emit domain event for cross-module lifecycle transitions (after DB commit)
        event = SaleCompletedEvent.create(
            tenant_id=tenant_id,
            sale_id=saved_sale.id,
            customer_id=customer_id,
            stage=stage.value,
            amount=amount,
            offer_id=offer_id,
        )
        EventBus.publish(event, session=self.repository.db)

        return saved_sale
