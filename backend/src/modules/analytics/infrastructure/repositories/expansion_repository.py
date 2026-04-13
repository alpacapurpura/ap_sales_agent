"""Expansion metrics repository -- CRM queries for Stage 6 (Expansion).

Classifies EXPANSION sales as renewals (subscription_cycle metadata) vs upsells.
Queries churn data from LifecycleTransitionModel.
All queries use SQLAlchemy 2.0 select() syntax with tenant_id filtering.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel
from src.modules.crm.infrastructure.models.lifecycle_transition_model import (
    LifecycleTransitionModel,
)
from src.modules.crm.infrastructure.models.sale_model import SaleModel
from src.shared.domain.enums import LifecycleStage, SaleStage, SaleStatus


class ExpansionMetricsRepository:
    """Aggregate expansion-stage metrics from CRM tables."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_expansion_sales_grouped(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, list[tuple]]:
        """Return expansion sales grouped as renewals vs upsells.

        Classification:
        - renewal: metadata_info->>'event_name' = 'subscription_cycle'
        - upsell: everything else in EXPANSION stage

        Returns:
            {"renewals": [(offer_id, count, amount, currency), ...],
             "upsells": [(offer_id, count, amount, currency), ...]}
        """
        base_where = [
            SaleModel.tenant_id == tenant_id,
            SaleModel.stage == SaleStage.EXPANSION,
            SaleModel.status == SaleStatus.COMPLETED,
            SaleModel.occurred_at >= start_date,
            SaleModel.occurred_at <= end_date,
        ]

        # Renewals: metadata_info->>'event_name' = 'subscription_cycle'
        renewal_stmt = (
            select(
                SaleModel.offer_id,
                func.count(SaleModel.id).label("count"),
                func.coalesce(func.sum(SaleModel.amount), 0.0).label("total_amount"),
                SaleModel.currency,
            )
            .where(
                *base_where,
                func.jsonb_extract_path_text(SaleModel.metadata_info, "event_name") == "subscription_cycle",
            )
            .group_by(SaleModel.offer_id, SaleModel.currency)
        )
        renewals = self.db.execute(renewal_stmt).all()

        # Upsells: EXPANSION sales that are NOT subscription_cycle
        upsell_stmt = (
            select(
                SaleModel.offer_id,
                func.count(SaleModel.id).label("count"),
                func.coalesce(func.sum(SaleModel.amount), 0.0).label("total_amount"),
                SaleModel.currency,
            )
            .where(
                *base_where,
                func.coalesce(
                    func.jsonb_extract_path_text(SaleModel.metadata_info, "event_name"),
                    "",
                )
                != "subscription_cycle",
            )
            .group_by(SaleModel.offer_id, SaleModel.currency)
        )
        upsells = self.db.execute(upsell_stmt).all()

        return {
            "renewals": [(r[0], int(r[1]), float(r[2]), r[3]) for r in renewals],
            "upsells": [(u[0], int(u[1]), float(u[2]), u[3]) for u in upsells],
        }

    def get_churn_data_by_offer(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[tuple]:
        """Get churn counts grouped by the churned customer's last known offer.

        Joins LifecycleTransitionModel (to_stage=CHURNED) with SaleModel
        to find which offer the churned customer was subscribed to.

        Returns: [(offer_id, churn_count, lost_revenue, currency), ...]
        """
        # Subquery: get churned profile_ids in period
        churned_profiles = (
            select(LifecycleTransitionModel.profile_id).where(
                LifecycleTransitionModel.tenant_id == tenant_id,
                LifecycleTransitionModel.to_stage == LifecycleStage.CHURNED,
                LifecycleTransitionModel.occurred_at >= start_date,
                LifecycleTransitionModel.occurred_at <= end_date,
            )
        ).subquery()

        # Join with most recent EXPANSION sale per customer to get offer_id and lost revenue
        # Use a window function to get the last sale per customer
        last_sale = (
            select(
                SaleModel.customer_id,
                SaleModel.offer_id,
                SaleModel.amount,
                SaleModel.currency,
                func.row_number()
                .over(
                    partition_by=SaleModel.customer_id,
                    order_by=SaleModel.occurred_at.desc(),
                )
                .label("rn"),
            ).where(
                SaleModel.tenant_id == tenant_id,
                SaleModel.stage == SaleStage.EXPANSION,
                SaleModel.status == SaleStatus.COMPLETED,
                SaleModel.customer_id.in_(select(churned_profiles.c.profile_id)),
            )
        ).subquery()

        stmt = (
            select(
                last_sale.c.offer_id,
                func.count(distinct(last_sale.c.customer_id)).label("churn_count"),
                func.coalesce(func.sum(last_sale.c.amount), 0.0).label("lost_revenue"),
                last_sale.c.currency,
            )
            .where(last_sale.c.rn == 1)
            .group_by(last_sale.c.offer_id, last_sale.c.currency)
        )
        results = self.db.execute(stmt).all()
        return [(r[0], int(r[1]), float(r[2]), r[3]) for r in results]

    def get_total_churn_count(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Count distinct profiles that churned in the period."""
        stmt = select(func.count(distinct(LifecycleTransitionModel.profile_id))).where(
            LifecycleTransitionModel.tenant_id == tenant_id,
            LifecycleTransitionModel.to_stage == LifecycleStage.CHURNED,
            LifecycleTransitionModel.occurred_at >= start_date,
            LifecycleTransitionModel.occurred_at <= end_date,
        )
        result = self.db.execute(stmt).scalar()
        return result or 0

    def get_active_customer_count(self, tenant_id: UUID) -> int:
        """Count active customers (CUSTOMER or EVANGELIST lifecycle stage)."""
        stmt = select(func.count(CustomerProfileModel.id)).where(
            CustomerProfileModel.tenant_id == tenant_id,
            CustomerProfileModel.lifecycle_stage.in_(
                [
                    LifecycleStage.CUSTOMER,
                    LifecycleStage.EVANGELIST,
                ],
            ),
        )
        result = self.db.execute(stmt).scalar()
        return result or 0

    def get_avg_ltv(self, tenant_id: UUID) -> tuple[float, str]:
        """Average lifetime_value for active customers.

        Returns: (avg_ltv, currency_from_most_recent_sale)
        """
        stmt = select(func.avg(CustomerProfileModel.lifetime_value)).where(
            CustomerProfileModel.tenant_id == tenant_id,
            CustomerProfileModel.lifecycle_stage.in_(
                [
                    LifecycleStage.CUSTOMER,
                    LifecycleStage.EVANGELIST,
                ],
            ),
            CustomerProfileModel.lifetime_value > 0,
        )
        avg_val = self.db.execute(stmt).scalar()

        # Get currency from most recent completed sale
        currency_stmt = (
            select(SaleModel.currency)
            .where(
                SaleModel.tenant_id == tenant_id,
                SaleModel.status == SaleStatus.COMPLETED,
            )
            .order_by(SaleModel.occurred_at.desc())
            .limit(1)
        )
        currency = self.db.execute(currency_stmt).scalar()

        return (round(float(avg_val), 2) if avg_val else 0.0, currency or "MXN")

    def get_expansion_customer_count(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Count distinct customers with EXPANSION sales (upsells only, not renewals)."""
        stmt = select(func.count(distinct(SaleModel.customer_id))).where(
            SaleModel.tenant_id == tenant_id,
            SaleModel.stage == SaleStage.EXPANSION,
            SaleModel.status == SaleStatus.COMPLETED,
            SaleModel.occurred_at >= start_date,
            SaleModel.occurred_at <= end_date,
            func.coalesce(
                func.jsonb_extract_path_text(SaleModel.metadata_info, "event_name"),
                "",
            )
            != "subscription_cycle",
        )
        result = self.db.execute(stmt).scalar()
        return result or 0
