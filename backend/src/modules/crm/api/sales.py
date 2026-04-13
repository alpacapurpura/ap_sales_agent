from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.crm.application.services.sale_service import SaleService
from src.modules.crm.domain.enums import PaymentMethod, SaleStage, SaleStatus
from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel
from src.modules.crm.infrastructure.repositories.sale_repository import SaleRepository
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

router = APIRouter(tags=["Sales"])


class TickerItem(BaseModel):
    id: UUID
    amount: float
    currency: str
    customer_name: str | None = None
    stage: str
    occurred_at: datetime
    offer_name: str | None = None


class SaleCreate(BaseModel):
    customer_id: UUID
    offer_id: UUID
    amount: float
    payment_method: PaymentMethod
    transaction_id: str | None = None
    source: str | None = "MANUAL"
    metadata: dict | None = Field(default_factory=dict)
    status: SaleStatus | None = SaleStatus.COMPLETED


class SaleResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    customer_id: UUID
    offer_id: UUID
    transaction_id: str | None
    amount: float
    currency: str
    status: SaleStatus
    stage: SaleStage
    source: str
    payment_method: PaymentMethod | None
    metadata: dict
    occurred_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


@router.post("/", response_model=SaleResponse)
def create_sale(
    sale_in: SaleCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    service = SaleService(db)
    # Instantiate service logic
    new_sale = service.create_sale(
        tenant_id=user.tenant_id,
        customer_id=sale_in.customer_id,
        offer_id=sale_in.offer_id,
        amount=sale_in.amount,
        payment_method=sale_in.payment_method,
        transaction_id=sale_in.transaction_id,
        source=sale_in.source,
        metadata=sale_in.metadata,
        status=sale_in.status,
    )

    return SaleResponse(
        id=new_sale.id,
        tenant_id=new_sale.tenant_id,
        customer_id=new_sale.customer_id,
        offer_id=new_sale.offer_id,
        transaction_id=new_sale.transaction_id,
        amount=new_sale.amount,
        currency=new_sale.currency,
        status=new_sale.status,
        stage=new_sale.stage,
        source=new_sale.source,
        payment_method=new_sale.payment_method,
        metadata=new_sale.metadata,
        occurred_at=new_sale.occurred_at,
        created_at=new_sale.created_at or datetime.now(UTC),  # Fallback if created_at is None immediately
    )


@router.get("/ticker", response_model=list[TickerItem])
async def get_ticker(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    range_: Annotated[Literal["today", "week", "30d", "all"], Query(alias="range")] = "30d",
):
    repo = SaleRepository(db)
    now = datetime.now(UTC)

    if range_ == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_ == "week":
        start = now - timedelta(days=7)
    elif range_ == "30d":
        start = now - timedelta(days=30)
    else:
        start = datetime.min.replace(tzinfo=UTC)

    end = now

    sales = repo.get_sales_by_date_range(user.tenant_id, start, end)

    # Enrich with Customer and Offer Names
    customer_ids = [s.customer_id for s in sales]
    offer_ids = [s.offer_id for s in sales]

    customer_map = {}
    if customer_ids:
        customers = (
            db.execute(
                select(CustomerProfileModel).where(
                    CustomerProfileModel.id.in_(customer_ids),
                ),
            )
            .scalars()
            .all()
        )
        for c in customers:
            customer_map[c.id] = c.full_name or "Unknown Customer"

    offer_map: dict[UUID, str] = {}
    if offer_ids:
        rows = (
            db.execute(
                sa_text("SELECT id, name FROM products WHERE id = ANY(:ids)"),
                {"ids": list(offer_ids)},
            )
            .mappings()
            .all()
        )
        for r in rows:
            offer_map[r["id"]] = r["name"] or "Unknown Offer"

    return [
        TickerItem(
            id=s.id,
            amount=s.amount,
            currency=s.currency,
            customer_name=customer_map.get(s.customer_id, "Unknown Customer"),
            stage=s.stage.value,
            occurred_at=s.occurred_at,
            offer_name=offer_map.get(s.offer_id, "Unknown Offer"),
        )
        for s in sales
    ]
