"""Adoption metrics repository -- CRM aggregate queries for Stage 5.

Queries CustomerProfileModel + SaleModel + JourneyEventModel for:
- Customer health (active vs inactive) grouped by offer
- Time-to-Value (TTV) per offer
- Total customer and sales counts for MiniFunnel
- Refund count and amount (source-agnostic)

All queries use SQLAlchemy 2.0 select() syntax with tenant_id isolation.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from src.modules.crm.infrastructure.models.customer_model import (
    CustomerProfileModel,
    JourneyEventModel,
)
from src.modules.crm.infrastructure.models.sale_model import SaleModel
from src.shared.domain.enums import LifecycleStage, SaleStage, SaleStatus

# Lifecycle stages that represent post-purchase customers
_CUSTOMER_STAGES = [
    LifecycleStage.CUSTOMER,
    LifecycleStage.EVANGELIST,
    LifecycleStage.CHURNED,
]


class AdoptionMetricsRepository:
    """CRM aggregate queries for adoption (Stage 5) metrics."""

    def __init__(self, db: Session):
        self.db = db

    def get_customer_health_by_offer(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[tuple]:
        """Count active vs inactive customers grouped by offer_id.

        Joins SaleModel (CONVERSION + COMPLETED) with CustomerProfileModel
        filtered to post-purchase lifecycle stages. Returns tuples of:
        (offer_id, total_count, active_count, inactive_count)
        """
        stmt = (
            select(
                SaleModel.offer_id,
                func.count(distinct(CustomerProfileModel.id)).label("total"),
                func.count(distinct(CustomerProfileModel.id))
                .filter(CustomerProfileModel.is_inactive == False)  # noqa: E712
                .label("active"),
                func.count(distinct(CustomerProfileModel.id))
                .filter(CustomerProfileModel.is_inactive == True)  # noqa: E712
                .label("inactive"),
            )
            .join(
                CustomerProfileModel,
                SaleModel.customer_id == CustomerProfileModel.id,
            )
            .where(
                SaleModel.tenant_id == tenant_id,
                CustomerProfileModel.tenant_id == tenant_id,
                SaleModel.status == SaleStatus.COMPLETED,
                SaleModel.stage == SaleStage.CONVERSION,
                CustomerProfileModel.lifecycle_stage.in_(_CUSTOMER_STAGES),
            )
            .group_by(SaleModel.offer_id)
        )
        return self.db.execute(stmt).all()

    def get_avg_ttv_by_offer(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, float]:
        """Average Time-to-Value per offer_id.

        TTV = days from first_conversion_at to first post-purchase journey_event.
        Excludes customers without post-purchase events.
        Returns dict mapping offer_id string to avg TTV days (rounded to 1 decimal).
        """
        # Subquery: first post-purchase event per customer
        first_event = (
            select(
                JourneyEventModel.profile_id,
                func.min(JourneyEventModel.occurred_at).label("first_event_at"),
            )
            .where(JourneyEventModel.tenant_id == tenant_id)
            .group_by(JourneyEventModel.profile_id)
            .subquery()
        )

        stmt = (
            select(
                SaleModel.offer_id,
                func.avg(
                    func.extract(
                        "epoch",
                        first_event.c.first_event_at
                        - CustomerProfileModel.first_conversion_at,
                    )
                    / 86400
                ).label("avg_ttv"),
            )
            .join(
                CustomerProfileModel,
                SaleModel.customer_id == CustomerProfileModel.id,
            )
            .outerjoin(
                first_event,
                CustomerProfileModel.id == first_event.c.profile_id,
            )
            .where(
                SaleModel.tenant_id == tenant_id,
                CustomerProfileModel.tenant_id == tenant_id,
                SaleModel.stage == SaleStage.CONVERSION,
                SaleModel.status == SaleStatus.COMPLETED,
                CustomerProfileModel.first_conversion_at.isnot(None),
                first_event.c.first_event_at > CustomerProfileModel.first_conversion_at,
            )
            .group_by(SaleModel.offer_id)
        )
        results = self.db.execute(stmt).all()
        return {
            str(row[0]): round(float(row[1]), 1)
            for row in results
            if row[1] is not None
        }

    def get_total_customers_and_sales(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> tuple[int, int]:
        """Return (total_customers, total_sales_count) for MiniFunnel.

        total_customers: distinct profiles with lifecycle_stage in CUSTOMER/EVANGELIST/CHURNED
        total_sales_count: count of CONVERSION + COMPLETED sales
        """
        # Total customers
        cust_stmt = select(func.count(distinct(CustomerProfileModel.id))).where(
            CustomerProfileModel.tenant_id == tenant_id,
            CustomerProfileModel.lifecycle_stage.in_(_CUSTOMER_STAGES),
        )
        total_customers = self.db.execute(cust_stmt).scalar() or 0

        # Total sales count (CONVERSION + COMPLETED)
        sales_stmt = select(func.count(SaleModel.id)).where(
            SaleModel.tenant_id == tenant_id,
            SaleModel.stage == SaleStage.CONVERSION,
            SaleModel.status == SaleStatus.COMPLETED,
        )
        total_sales = self.db.execute(sales_stmt).scalar() or 0

        return (total_customers, total_sales)

    def get_refunds(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> tuple[int, float, str]:
        """Return (refund_count, refund_total_amount, currency) for refunded sales.

        Source-agnostic per CONTEXT.md -- no filtering by source column.
        """
        stmt = (
            select(
                func.count(SaleModel.id).label("count"),
                func.coalesce(func.sum(SaleModel.amount), 0.0).label("total"),
                SaleModel.currency,
            )
            .where(
                SaleModel.tenant_id == tenant_id,
                SaleModel.status == SaleStatus.REFUNDED,
            )
            .group_by(SaleModel.currency)
        )
        results = self.db.execute(stmt).all()

        if not results:
            return (0, 0.0, "USD")

        # Sum across all currencies (pick most common currency for display)
        total_count = sum(r[0] for r in results)
        total_amount = sum(float(r[1]) for r in results)
        # Use the currency with the most refunds
        primary_currency = max(results, key=lambda r: r[0])[2] or "USD"

        return (total_count, total_amount, primary_currency)
