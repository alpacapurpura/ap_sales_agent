"""Generic cost service for any funnel stage with per-group breakdown.

Extends the CaptureCostService pattern to support nurture stage costs,
including retargeting ad spend from MetricAggregationModel and per-group
cost/MQL calculations (locked CONTEXT.md decision).
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.modules.analytics.infrastructure.models.channel_cost_model import (
    ChannelCostSettingModel,
)

logger = logging.getLogger(__name__)

# Retargeting channel slugs for spend lookup
_RETARGETING_SLUGS = {"meta-retargeting", "google-retargeting", "tiktok-retargeting"}

# Automation channel slugs for cost lookup
_AUTOMATION_SLUGS = {"mailerlite", "ai-sdr"}


class StageCostService:
    """Generic cost service for any stage (replaces stage-specific services).

    Supports per-group cost breakdown: Retargeting cost/MQL and Automation cost/MQL
    in group headers per CONTEXT.md decision.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_channel_costs(
        self,
        tenant_id: UUID,
        stage: str = "nurture",
    ) -> dict[str, float]:
        """Get total monthly cost per channel slug from channel_cost_settings.

        Sums multiple cost entries per channel (platform + agency + tool).
        Returns: {"mailerlite": 29.0, "ai-sdr": 15.0, ...}
        """
        stmt = (
            select(
                ChannelCostSettingModel.channel_slug,
                func.sum(ChannelCostSettingModel.monthly_amount).label("total"),
            )
            .where(
                ChannelCostSettingModel.tenant_id == tenant_id,
                ChannelCostSettingModel.is_active.is_(True),
                ChannelCostSettingModel.deleted_at.is_(None),
                ChannelCostSettingModel.proration_category.is_(None),
            )
            .group_by(ChannelCostSettingModel.channel_slug)
        )
        rows = self.db.execute(stmt).all()
        return {row.channel_slug: float(row.total) for row in rows}

    def get_retargeting_spend(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, float]:
        """Get retargeting ad spend from MetricAggregationModel.

        Queries spend metric for meta-retargeting, google-retargeting,
        tiktok-retargeting channels.
        Returns: {'meta-retargeting': 450.0, 'google-retargeting': 200.0, ...}
        """
        from src.modules.analytics.infrastructure.models.metric_aggregation_model import (
            MetricAggregationModel,
        )

        stmt = (
            select(
                MetricAggregationModel.channel_slug,
                func.coalesce(func.sum(MetricAggregationModel.value), 0.0).label(
                    "total",
                ),
            )
            .where(
                MetricAggregationModel.tenant_id == tenant_id,
                MetricAggregationModel.channel_slug.in_(_RETARGETING_SLUGS),
                MetricAggregationModel.metric_name == "spend",
                MetricAggregationModel.period_type == "last_30_days",
            )
            .group_by(MetricAggregationModel.channel_slug)
        )
        rows = self.db.execute(stmt).all()
        return {row.channel_slug: float(row.total) for row in rows}

    def calculate_cost_per_mql(
        self,
        total_costs: float,
        total_mqls: int,
    ) -> float | None:
        """Cost per MQL = total costs / total MQLs. Returns None if mqls == 0."""
        if total_mqls == 0:
            return None
        return round(total_costs / total_mqls, 2)

    def get_group_cost_per_mql(
        self,
        group: str,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
        total_mqls: int,
    ) -> float | None:
        """Calculate cost/MQL for a specific group.

        For 'retargeting': sum retargeting ad spend only.
        For 'automation': sum Mailerlite subscription (manual) + AI SDR token costs.
        Returns None if total_mqls == 0.

        This powers the per-group cost breakdown in ChannelGroup headers
        per CONTEXT.md decision.
        """
        if total_mqls == 0:
            return None

        if group == "retargeting":
            retargeting_spend = self.get_retargeting_spend(
                tenant_id,
                start_date,
                end_date,
            )
            group_cost = sum(retargeting_spend.values())
        elif group == "automation":
            # Get manual costs for automation channels
            all_costs = self.get_channel_costs(tenant_id, "nurture")
            group_cost = sum(
                cost for slug, cost in all_costs.items() if slug in _AUTOMATION_SLUGS
            )
        else:
            logger.warning("Unknown cost group: %s", group)
            return None

        if group_cost == 0.0:
            return None

        return round(group_cost / total_mqls, 2)

    def get_total_funnel_investment(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> tuple[float, bool]:
        """Sum all pre-sale funnel investment (Stages 0-3) for CAC calculation.

        Returns: (total_cost, is_complete)
        - is_complete=False when total is 0.0 (likely unconfigured costs)

        Stage 0: Ad spend from MetricAggregationModel (meta-ads, google-ads, tiktok-ads)
        Stage 1: Capture channel costs (platform + agency + LLM tokens)
        Stage 2: Nurture costs (retargeting spend + automation tools)
        Stage 3: Opportunity costs (Shopify, scheduling tools -- manual config)
        """
        from src.modules.analytics.infrastructure.models.metric_aggregation_model import (
            MetricAggregationModel,
        )

        # Stage 0: paid ad spend
        ad_slugs = {"meta-ads", "google-ads", "tiktok-ads"}
        stmt_ads = select(
            func.coalesce(func.sum(MetricAggregationModel.value), 0.0),
        ).where(
            MetricAggregationModel.tenant_id == tenant_id,
            MetricAggregationModel.channel_slug.in_(ad_slugs),
            MetricAggregationModel.metric_name == "spend",
            MetricAggregationModel.period_type == "last_30_days",
        )
        ad_spend = float(self.db.execute(stmt_ads).scalar() or 0.0)

        # Stages 1-3: manual channel costs (all stages)
        all_manual_costs = self.get_channel_costs(tenant_id)
        manual_total = sum(all_manual_costs.values())

        # Stage 2: retargeting ad spend
        retargeting = self.get_retargeting_spend(tenant_id, start_date, end_date)
        retargeting_total = sum(retargeting.values())

        total = ad_spend + manual_total + retargeting_total
        is_complete = total > 0.0

        return total, is_complete
