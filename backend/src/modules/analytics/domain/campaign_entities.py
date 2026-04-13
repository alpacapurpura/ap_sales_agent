"""Domain entities for campaign management.

Value objects and enums — no framework imports.
"""

from __future__ import annotations

from enum import StrEnum


class CampaignObjective(StrEnum):
    """Meta ODAX (Outcome-Driven Ad Experiences) objectives."""

    OUTCOME_AWARENESS = "OUTCOME_AWARENESS"
    OUTCOME_ENGAGEMENT = "OUTCOME_ENGAGEMENT"
    OUTCOME_TRAFFIC = "OUTCOME_TRAFFIC"
    OUTCOME_LEADS = "OUTCOME_LEADS"
    OUTCOME_SALES = "OUTCOME_SALES"
    OUTCOME_APP_PROMOTION = "OUTCOME_APP_PROMOTION"
    # Legacy objectives (still returned by API for old campaigns)
    CONVERSIONS = "CONVERSIONS"
    LINK_CLICKS = "LINK_CLICKS"
    REACH = "REACH"
    BRAND_AWARENESS = "BRAND_AWARENESS"
    VIDEO_VIEWS = "VIDEO_VIEWS"
    POST_ENGAGEMENT = "POST_ENGAGEMENT"
    MESSAGES = "MESSAGES"
    LEAD_GENERATION = "LEAD_GENERATION"
    UNKNOWN = "UNKNOWN"


class CampaignStatus(StrEnum):
    """Enumerate campaign status values."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DELETED = "DELETED"
    ARCHIVED = "ARCHIVED"
    IN_PROCESS = "IN_PROCESS"
    WITH_ISSUES = "WITH_ISSUES"


class EffectiveStatus(StrEnum):
    """Effective status includes inherited states from parent objects."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DELETED = "DELETED"
    ARCHIVED = "ARCHIVED"
    IN_PROCESS = "IN_PROCESS"
    WITH_ISSUES = "WITH_ISSUES"
    PENDING_REVIEW = "PENDING_REVIEW"
    DISAPPROVED = "DISAPPROVED"
    CAMPAIGN_PAUSED = "CAMPAIGN_PAUSED"
    ADSET_PAUSED = "ADSET_PAUSED"
    PREAPPROVED = "PREAPPROVED"


class BidStrategy(StrEnum):
    """Enumerate bid strategy values."""

    LOWEST_COST_WITHOUT_CAP = "LOWEST_COST_WITHOUT_CAP"
    LOWEST_COST_WITH_BID_CAP = "LOWEST_COST_WITH_BID_CAP"
    COST_CAP = "COST_CAP"
    LOWEST_COST_WITH_MIN_ROAS = "LOWEST_COST_WITH_MIN_ROAS"


class LearningStage(StrEnum):
    """Enumerate learning stage values."""

    LEARNING = "LEARNING"
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"


class RecommendationSource(StrEnum):
    """Where the recommendation came from."""

    ACCOUNT = "account"  # GET /act_{id}/recommendations
    CAMPAIGN = "campaign"  # campaign.recommendations field
    AD_SET = "ad_set"  # adset.recommendations field
    AD = "ad"  # ad.recommendations field
