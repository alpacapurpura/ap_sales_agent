"""DTOs for campaign management API responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CampaignDTO(BaseModel):
    external_id: str
    name: str
    objective: str | None = None
    status: str | None = None
    effective_status: str | None = None
    bid_strategy: str | None = None
    daily_budget: int | None = None
    lifetime_budget: int | None = None
    budget_remaining: int | None = None
    buying_type: str | None = None
    start_time: datetime | None = None
    stop_time: datetime | None = None
    ad_sets_count: int = 0
    ads_count: int = 0


class AdSetDTO(BaseModel):
    external_id: str
    campaign_external_id: str
    name: str
    status: str | None = None
    effective_status: str | None = None
    optimization_goal: str | None = None
    targeting_summary: dict | None = None
    learning_stage: str | None = None
    daily_budget: int | None = None
    ads_count: int = 0


class AdDTO(BaseModel):
    external_id: str
    name: str
    status: str | None = None
    effective_status: str | None = None
    creative_thumbnail_url: str | None = None
    creative_title: str | None = None
    creative_cta: str | None = None
    preview_shareable_link: str | None = None


class RecommendationDTO(BaseModel):
    recommendation_type: str
    source: str
    title: str | None = None
    body: str | None = None
    importance: str | None = None
    lift_estimate: str | None = None
    opportunity_score: float | None = None
    url: str | None = None
    object_ids: list = []


class CampaignOverviewDTO(BaseModel):
    campaigns: list[CampaignDTO]
    recommendations: list[RecommendationDTO]
    total_campaigns: int
    active_campaigns: int
    last_synced: datetime | None = None


class CampaignMetricsDTO(BaseModel):
    """Aggregated metrics for a single campaign."""

    spend: float = 0.0
    conversions: float = 0.0
    cpa: float | None = None
    roas: float | None = None
    ctr: float | None = None
    cpc: float | None = None
    cpm: float | None = None
    frequency: float | None = None
    impressions: float = 0.0
    clicks: float = 0.0
    reach: float = 0.0


class CampaignWithMetricsDTO(BaseModel):
    """Campaign metadata + aggregated performance metrics."""

    external_id: str
    name: str
    objective: str | None = None
    status: str | None = None
    effective_status: str | None = None
    daily_budget: int | None = None
    lifetime_budget: int | None = None
    budget_remaining: int | None = None
    start_time: datetime | None = None
    stop_time: datetime | None = None
    ad_sets_count: int = 0
    ads_count: int = 0
    metrics: CampaignMetricsDTO = CampaignMetricsDTO()
    health: str = "good"  # "good" | "warning" | "critical"


class CampaignPerformanceDTO(BaseModel):
    """Full campaign performance dashboard response."""

    campaigns: list[CampaignWithMetricsDTO]
    recommendations: list[RecommendationDTO]
    total_campaigns: int
    active_campaigns: int
    currency: str | None = None
    last_synced: datetime | None = None


# ---------------------------------------------------------------------------
# Creatives / Ad Gallery DTOs
# ---------------------------------------------------------------------------


class AdPerformanceDTO(BaseModel):
    """Single ad entry for the ad gallery with creative details."""

    external_id: str
    name: str
    campaign_name: str | None = None
    campaign_external_id: str | None = None
    status: str | None = None
    effective_status: str | None = None
    creative_thumbnail_url: str | None = None
    creative_title: str | None = None
    creative_cta: str | None = None
    preview_shareable_link: str | None = None


class VideoRetentionDTO(BaseModel):
    """Video retention funnel metrics (aggregate across all ads)."""

    plays: float = 0
    p25: float = 0
    p50: float = 0
    p75: float = 0
    p100: float = 0
    views_30s: float = 0
    avg_watch_time: float = 0


class CreativesOverviewDTO(BaseModel):
    """Ad gallery + video retention overview response."""

    ads: list[AdPerformanceDTO] = []
    video_retention: VideoRetentionDTO = VideoRetentionDTO()
    total_ads: int = 0


# Rebuild models that reference TYPE_CHECKING-only imports (datetime)
# so Pydantic can resolve forward references at runtime.
def _rebuild_models() -> None:
    import datetime as _dt

    ns = {"datetime": _dt.datetime}
    CampaignDTO.model_rebuild(_types_namespace=ns)
    CampaignOverviewDTO.model_rebuild(_types_namespace=ns)
    CampaignWithMetricsDTO.model_rebuild(_types_namespace=ns)
    CampaignPerformanceDTO.model_rebuild(_types_namespace=ns)


_rebuild_models()


# ---------------------------------------------------------------------------
# Ad-Level Performance DTOs
# ---------------------------------------------------------------------------


class AdMetricsDTO(BaseModel):
    """Single ad with performance metrics for the Creativos tab."""

    ad_id: str
    ad_name: str
    campaign_name: str | None = None
    campaign_external_id: str | None = None
    format_type: str = "unknown"  # "video" | "carousel" | "image" | "unknown"
    thumbnail_url: str | None = None
    preview_url: str | None = None
    creative_body: str | None = None
    creative_cta: str | None = None
    effective_status: str | None = None
    spend: float = 0.0
    impressions: float = 0.0
    clicks: float = 0.0
    conversions: float = 0.0
    roas: float | None = None
    cpa: float | None = None
    ctr: float | None = None
    cpc: float | None = None
    performance_tag: str = "average"  # "top_performer" | "average" | "underperformer"


class AdPerformanceListDTO(BaseModel):
    """Response for ad-level performance endpoint."""

    ads: list[AdMetricsDTO] = []
    period: str
    total_ads: int = 0
    currency: str | None = None


class FormatComparisonItemDTO(BaseModel):
    """Aggregated metrics for a single ad format type."""

    format_type: str
    emoji: str  # e.g. movie camera, framed picture, camera
    ad_count: int = 0
    avg_ctr: float = 0.0
    avg_cpa: float | None = None
    avg_roas: float | None = None
    total_spend: float = 0.0
    performance_score: float = 0.0  # 0-100 normalized


class FormatComparisonDTO(BaseModel):
    """Response for format comparison endpoint."""

    formats: list[FormatComparisonItemDTO] = []
    period: str
    currency: str | None = None
