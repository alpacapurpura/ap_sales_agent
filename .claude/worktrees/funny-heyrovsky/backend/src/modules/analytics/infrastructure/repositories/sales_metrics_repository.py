"""Sales metrics aggregation from CRM SaleModel.

Uses SQLAlchemy 2.0 select() syntax. All queries use the modern API.
Groups completed sales by stage, offer_id, source, currency for revenue analysis.
"""

from datetime import datetime
from typing import List, NamedTuple
from uuid import UUID

from sqlalchemy import func, select, distinct
from sqlalchemy.orm import Session

from src.modules.crm.infrastructure.models.sale_model import SaleModel
from src.modules.crm.domain.enums import SaleStatus, SaleStage


class SaleAggregation(NamedTuple):
    stage: str
    offer_id: UUID
    source: str
    currency: str
    count: int
    total_revenue: float
    unique_customers: int


class SalesMetricsRepository:
    """Aggregate completed sales by stage, offer_id, source, currency."""

    def __init__(self, db: Session):
        self.db = db

    def get_sales_summary(
        self, tenant_id: UUID, start_date: datetime, end_date: datetime
    ) -> List[SaleAggregation]:
        """Aggregate completed sales by stage, offer_id, source, currency."""
        stmt = (
            select(
                SaleModel.stage,
                SaleModel.offer_id,
                SaleModel.source,
                SaleModel.currency,
                func.count(SaleModel.id).label("count"),
                func.coalesce(func.sum(SaleModel.amount), 0.0).label("total_revenue"),
                func.count(distinct(SaleModel.customer_id)).label("unique_customers"),
            )
            .where(
                SaleModel.tenant_id == tenant_id,
                SaleModel.status == SaleStatus.COMPLETED,
                SaleModel.occurred_at >= start_date,
                SaleModel.occurred_at <= end_date,
            )
            .group_by(
                SaleModel.stage,
                SaleModel.offer_id,
                SaleModel.source,
                SaleModel.currency,
            )
        )
        return self.db.execute(stmt).all()

    def get_total_conversion_customers(
        self, tenant_id: UUID, start_date: datetime, end_date: datetime
    ) -> int:
        """Count distinct customers with CONVERSION sales in period."""
        stmt = (
            select(func.count(distinct(SaleModel.customer_id)))
            .where(
                SaleModel.tenant_id == tenant_id,
                SaleModel.status == SaleStatus.COMPLETED,
                SaleModel.stage == SaleStage.CONVERSION,
                SaleModel.occurred_at >= start_date,
                SaleModel.occurred_at <= end_date,
            )
        )
        result = self.db.execute(stmt).scalar()
        return result or 0

    def get_total_sql_count(
        self, tenant_id: UUID, start_date: datetime, end_date: datetime
    ) -> int:
        """Count SQLs (Stage 3 pipeline) for mini funnel denominator.

        Uses lifecycle_transitions to count profiles that entered SQL stage.
        """
        from src.modules.crm.infrastructure.models.lifecycle_transition_model import (
            LifecycleTransitionModel,
        )
        from src.modules.crm.domain.enums import LifecycleStage

        stmt = (
            select(func.count(distinct(LifecycleTransitionModel.profile_id)))
            .where(
                LifecycleTransitionModel.tenant_id == tenant_id,
                LifecycleTransitionModel.to_stage == LifecycleStage.SQL,
                LifecycleTransitionModel.occurred_at >= start_date,
                LifecycleTransitionModel.occurred_at <= end_date,
            )
        )
        result = self.db.execute(stmt).scalar()
        return result or 0
