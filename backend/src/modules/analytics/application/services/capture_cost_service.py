"""Cost calculation service for capture (Stage 1) metrics.

Handles per-channel cost retrieval, agency cost proration, and CAL computation.
Queries ChannelCostSettingModel for manual costs and MetricAggregationModel for
Stage 0 paid channel spend.
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

# Paid channel slugs from Stage 0 (attraction) for spend lookup
_PAID_CHANNEL_SLUGS = {"meta-ads", "google-ads", "tiktok-ads", "yt-ads"}


class CaptureCostService:
    """Cost retrieval, proration, and CAL calculation for capture metrics."""

    def __init__(self, db: Session):
        self.db = db

    def get_channel_costs(
        self,
        tenant_id: UUID,
        stage: str = "capture",
    ) -> dict[str, float]:
        """Get total monthly cost per channel slug from channel_cost_settings.

        Sums multiple cost entries per channel (platform + agency + tool).
        Returns: {"mailerlite": 29.0, "whatsapp-inbound": 15.0, ...}
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
                ChannelCostSettingModel.proration_category.is_(
                    None
                ),  # exclude prorated costs
            )
            .group_by(ChannelCostSettingModel.channel_slug)
        )
        rows = self.db.execute(stmt).all()
        return {row.channel_slug: float(row.total) for row in rows}

    def get_total_stage0_spend(
        self,
        tenant_id: UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> float:
        """Get total Stage 0 paid channel spend from metric_aggregations table.

        Reads spend metric for meta-ads, google-ads, tiktok-ads, yt-ads channels.
        """
        from src.modules.analytics.infrastructure.models.metric_aggregation_model import (
            MetricAggregationModel,
        )

        stmt = select(func.coalesce(func.sum(MetricAggregationModel.value), 0.0)).where(
            MetricAggregationModel.tenant_id == tenant_id,
            MetricAggregationModel.channel_slug.in_(_PAID_CHANNEL_SLUGS),
            MetricAggregationModel.metric_name == "spend",
            MetricAggregationModel.period_type == "last_30_days",
        )
        result = self.db.execute(stmt).scalar()
        return float(result) if result else 0.0

    def calculate_cal(
        self,
        total_costs: float,
        total_leads: int,
    ) -> float | None:
        """CAL = total costs / total leads. Returns None if leads == 0."""
        if total_leads == 0:
            return None
        return round(total_costs / total_leads, 2)

    def get_prorated_agency_costs(
        self,
        tenant_id: UUID,
        connected_channels: list[str],
    ) -> dict[str, float]:
        """Distribute agency costs across channels based on proration_category.

        Categories:
        - organic_management: evenly across connected organic social channels
        - paid_management: evenly across connected paid channels
        - video: evenly across video-capable channels (ig-dm, tiktok-dm)
        - full_service: evenly across all connected channels
        """
        stmt = select(ChannelCostSettingModel).where(
            ChannelCostSettingModel.tenant_id == tenant_id,
            ChannelCostSettingModel.is_active.is_(True),
            ChannelCostSettingModel.deleted_at.is_(None),
            ChannelCostSettingModel.proration_category.isnot(None),
        )
        rows = self.db.execute(stmt).scalars().all()

        if not rows or not connected_channels:
            return {}

        # Category-to-channel mapping for capture stage
        _CATEGORY_CHANNELS = {
            "organic_management": {"ig-dm", "fb-messenger", "tiktok-dm"},
            "paid_management": _PAID_CHANNEL_SLUGS,
            "video": {"ig-dm", "tiktok-dm"},
            "full_service": None,  # all connected channels
        }

        result: dict[str, float] = {}
        connected_set = set(connected_channels)

        for cost_entry in rows:
            category = cost_entry.proration_category
            eligible = _CATEGORY_CHANNELS.get(category)

            if eligible is None:
                # full_service -> all connected
                target_channels = connected_set
            else:
                target_channels = eligible & connected_set

            if not target_channels:
                continue

            per_channel = cost_entry.monthly_amount / len(target_channels)
            for ch_slug in target_channels:
                result[ch_slug] = result.get(ch_slug, 0.0) + per_channel

        return result
