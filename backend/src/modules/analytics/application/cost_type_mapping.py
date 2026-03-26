"""Maps (channel_slug, stage_slug) pairs to CostType for financial classification.

This mapping drives how each metric is classified in dashboard rollups:
- NEUTRAL: organic channels with no direct cost
- EXPENSE: operational tools with recurring cost
- INVESTMENT: paid advertising (expected ROI)
- REVENUE: sales/revenue channels
"""

import logging
from typing import Optional

from src.modules.analytics.domain.enums import CostType

logger = logging.getLogger(__name__)

# (channel_slug, stage_slug) -> CostType
COST_TYPE_MAP: dict[tuple[str, str], CostType] = {
    # Paid advertising = INVESTMENT (expected ROI)
    ("meta-ads", "attraction"): CostType.INVESTMENT,
    ("google-ads", "attraction"): CostType.INVESTMENT,
    ("tiktok-ads", "attraction"): CostType.INVESTMENT,
    ("yt-ads", "attraction"): CostType.INVESTMENT,
    # Organic social = NEUTRAL (no direct cost)
    ("ig-organic", "attraction"): CostType.NEUTRAL,
    ("yt-organic", "attraction"): CostType.NEUTRAL,
    ("fb-organic", "attraction"): CostType.NEUTRAL,
    ("tiktok-organic", "attraction"): CostType.NEUTRAL,
    ("linkedin-organic", "attraction"): CostType.NEUTRAL,
    ("google-organic", "attraction"): CostType.NEUTRAL,
    ("direct", "attraction"): CostType.NEUTRAL,
    ("ai-search-organic", "attraction"): CostType.NEUTRAL,
    # ManyChat channels
    ("manychat-comments", "attraction"): CostType.NEUTRAL,
    ("manychat-ig", "capture"): CostType.EXPENSE,
    ("manychat-wa", "capture"): CostType.EXPENSE,
    ("manychat-sequences", "nurture"): CostType.EXPENSE,
    ("manychat-bofu", "opportunity"): CostType.EXPENSE,
    # Operational tools = EXPENSE
    ("email-capture", "capture"): CostType.EXPENSE,
    ("email-nurture", "nurture"): CostType.EXPENSE,
    ("email-launch", "opportunity"): CostType.EXPENSE,
    ("email-delivery", "delivery"): CostType.EXPENSE,
    ("email-onboarding", "adoption"): CostType.EXPENSE,
    ("email-retention", "retention"): CostType.EXPENSE,
    ("email-upsell", "expansion"): CostType.EXPENSE,
    ("email-referral", "evangelization"): CostType.EXPENSE,
    ("cold-contact", "attraction"): CostType.EXPENSE,
    # Revenue channels
    ("shopify", "sales"): CostType.REVENUE,
}


def get_cost_type(channel_slug: str, stage_slug: str) -> Optional[CostType]:
    """Look up the CostType for a (channel, stage) pair.

    Returns None and logs a warning for unmapped pairs so new channels
    can be detected in monitoring without breaking the pipeline.
    """
    result = COST_TYPE_MAP.get((channel_slug, stage_slug))
    if result is None:
        logger.warning(
            "Unmapped cost type for channel_slug=%s, stage_slug=%s",
            channel_slug,
            stage_slug,
        )
    return result
