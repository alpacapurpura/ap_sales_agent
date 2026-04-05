from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.modules.crm.domain.enums import SaleStatus
from src.modules.crm.domain.sale import Sale
from src.modules.crm.infrastructure.models.sale_model import SaleModel


class SaleRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, model: SaleModel) -> Sale:
        return Sale(
            id=model.id,
            tenant_id=model.tenant_id,
            customer_id=model.customer_id,
            offer_id=model.offer_id,
            transaction_id=model.transaction_id,
            amount=model.amount,
            currency=model.currency,
            status=model.status,
            stage=model.stage,
            source=model.source,
            payment_method=model.payment_method,
            metadata=model.metadata_info or {},
            occurred_at=model.occurred_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def save(self, sale: Sale) -> Sale:
        model = (
            self.db.execute(select(SaleModel).where(SaleModel.id == sale.id))
            .scalars()
            .first()
        )
        if not model:
            model = SaleModel(id=sale.id)
            self.db.add(model)

        model.tenant_id = sale.tenant_id
        model.customer_id = sale.customer_id
        model.offer_id = sale.offer_id
        model.transaction_id = sale.transaction_id
        model.amount = sale.amount
        model.currency = sale.currency
        model.status = sale.status
        model.stage = sale.stage
        model.source = sale.source
        model.payment_method = sale.payment_method
        model.metadata_info = sale.metadata
        model.occurred_at = sale.occurred_at

        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def find_by_id(self, sale_id: UUID) -> Sale | None:
        model = (
            self.db.execute(select(SaleModel).where(SaleModel.id == sale_id))
            .scalars()
            .first()
        )
        return self._to_domain(model) if model else None

    def find_by_customer_id(self, customer_id: UUID) -> list[Sale]:
        models = (
            self.db.execute(
                select(SaleModel).where(SaleModel.customer_id == customer_id)
            )
            .scalars()
            .all()
        )
        return [self._to_domain(m) for m in models]

    def count_sales_by_customer(self, customer_id: UUID) -> int:
        return (
            self.db.execute(
                select(func.count(SaleModel.id)).where(
                    SaleModel.customer_id == customer_id,
                    SaleModel.status == SaleStatus.COMPLETED,
                )
            ).scalar()
            or 0
        )

    def get_sales_by_date_range(
        self, tenant_id: UUID, start: datetime, end: datetime
    ) -> list[Sale]:
        models = (
            self.db.execute(
                select(SaleModel)
                .where(
                    SaleModel.tenant_id == tenant_id,
                    SaleModel.status == SaleStatus.COMPLETED,
                    SaleModel.occurred_at >= start,
                    SaleModel.occurred_at <= end,
                )
                .order_by(SaleModel.occurred_at.desc())
            )
            .scalars()
            .all()
        )
        return [self._to_domain(m) for m in models]
