"""DTOs for the Email Intelligence Hub dashboard."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from src.modules.analytics.application.dto.channel_dashboard_dto import (
    BenchmarkRangeDTO,
    FunnelStepDTO,
    MetricKpiDTO,
    MetricTimeSeriesDTO,
)

# Re-export so callers can import everything from this module
__all__ = [
    "ActivityHeatmapCellDTO",
    "BenchmarkRangeDTO",
    "BounceBreakdownDTO",
    "CampaignsVsAutomationsDTO",
    "EmailAudienceResponseDTO",
    "EmailAutomationDTO",
    "EmailAutomationsResponseDTO",
    "EmailCampaignDTO",
    "EmailCampaignSummaryDTO",
    "EmailCampaignsResponseDTO",
    "EmailDashboardDTO",
    "EmailEngagementSegmentDTO",
    "EmailGrowthResponseDTO",
    "EmailHealthResponseDTO",
    "EmailHealthScoreDTO",
    "EmailHealthSubScoreDTO",
    "EmailSourcePerformanceDTO",
    "EmailTypePerformanceDTO",
    "EngagementDecayDTO",
    "FunnelStepDTO",
    "MetricKpiDTO",
    "MetricTimeSeriesDTO",
    "SegmentTypeMatrixCellDTO",
]


# -- Sidebar + Panorama -------------------------------------------------------


class EmailHealthSubScoreDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    area: str  # engagement | entregabilidad | crecimiento | contenido
    label: str
    score: int  # 0-100
    color: str  # green | yellow | red


class EmailHealthScoreDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total: int  # 0-100
    sub_scores: list[EmailHealthSubScoreDTO]


class EmailCampaignSummaryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    campaign_name: str
    campaign_subject: str | None = None
    campaign_type: (
        str  # newsletter | lanzamiento | promocion | contenido | reengagement
    )
    sent_count: int
    open_rate: float
    click_to_open_rate: float
    sent_date: str | None = None


class CampaignsVsAutomationsDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    campaigns_sent: int = 0
    campaigns_open_rate: float = 0.0
    campaigns_click_rate: float = 0.0
    campaigns_ctor: float = 0.0
    campaigns_unsubs: int = 0
    automations_sent: int = 0
    automations_open_rate: float = 0.0
    automations_click_rate: float = 0.0
    automations_ctor: float = 0.0
    automations_unsubs: int = 0


class EmailDashboardDTO(BaseModel):
    """Main sidebar + Panorama tab response."""

    model_config = ConfigDict(from_attributes=True)
    channel_slug: str
    channel_name: str
    provider_name: str | None = None  # "mailerlite", "mailchimp", etc.
    period: str
    health_score: EmailHealthScoreDTO
    kpis: list[MetricKpiDTO]
    time_series: list[MetricTimeSeriesDTO]
    funnel: list[FunnelStepDTO]
    best_campaign: EmailCampaignSummaryDTO | None = None
    worst_campaign: EmailCampaignSummaryDTO | None = None
    campaigns_vs_automations: CampaignsVsAutomationsDTO | None = None


# -- Campanas Tab --------------------------------------------------------------


class EmailCampaignDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    campaign_id: str
    campaign_name: str
    campaign_subject: str | None = None
    campaign_type: str
    sent_date: str | None = None
    emails_sent: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    click_to_open_rate: float = 0.0
    bounce_rate: float = 0.0
    unsubscribes: int = 0
    unique_opens: int = 0
    unique_clicks: int = 0


class EmailTypePerformanceDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    campaign_type: (
        str  # newsletter | lanzamiento | promocion | contenido | reengagement
    )
    campaign_count: int = 0
    total_sent: int = 0
    avg_open_rate: float = 0.0
    avg_ctor: float = 0.0
    total_unsubs: int = 0
    rank_label: str = ""  # "Mejor engagement", "2do mejor", etc.


class EmailCampaignsResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period: str
    type_performance: list[EmailTypePerformanceDTO]
    campaigns: list[EmailCampaignDTO]
    top_subjects: list[EmailCampaignSummaryDTO]


# -- Automatizaciones Tab -----------------------------------------------------


class EmailAutomationDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    automation_id: str
    name: str
    automation_type: str  # welcome | nurture | reengagement | post_compra | other
    status: str  # active | paused
    active_subscribers: int = 0
    completed: int = 0
    emails_sent: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    completion_rate: float = 0.0


class EmailAutomationsResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period: str
    kpis: list[MetricKpiDTO]
    automations: list[EmailAutomationDTO]


# -- Audiencia Tab -------------------------------------------------------------


class EmailEngagementSegmentDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    segment_name: str  # champions | activos | en_riesgo | dormidos
    label: str
    count: int = 0
    percentage: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    ctor: float = 0.0
    avg_days_inactive: float | None = None
    recommended_action: str = ""


class SegmentTypeMatrixCellDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    segment_name: str
    campaign_type: str
    open_rate: float = 0.0


class EmailSourcePerformanceDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    source: str  # landing_page | popup | checkout | import | api
    label: str
    subscriber_count: int = 0
    percentage: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    champions_pct: float = 0.0


class EngagementDecayDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period_label: str  # "0-30 dias", "31-90 dias", etc.
    open_rate: float = 0.0


class ActivityHeatmapCellDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    day_of_week: int  # 0=Monday, 6=Sunday
    hour_block: str  # "6-9", "9-12", "12-15", "15-18", "18-21", "21-24"
    open_rate: float = 0.0


class EmailAudienceResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period: str
    segments: list[EmailEngagementSegmentDTO]
    segment_type_matrix: list[SegmentTypeMatrixCellDTO]
    sources: list[EmailSourcePerformanceDTO]
    engagement_decay: list[EngagementDecayDTO]
    activity_heatmap: list[ActivityHeatmapCellDTO]


# -- Entregabilidad Tab -------------------------------------------------------


class BounceBreakdownDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    hard_bounces: int = 0
    soft_bounces: int = 0
    hard_bounce_rate: float = 0.0
    soft_bounce_rate: float = 0.0
    total_delivered: int = 0


class EmailHealthResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period: str
    campaigns_count: int = 0
    health_score: EmailHealthScoreDTO
    kpis: list[MetricKpiDTO]
    bounce_breakdown: BounceBreakdownDTO
    time_series: list[MetricTimeSeriesDTO]
    alerts: list[str]


# -- Crecimiento Tab -----------------------------------------------------------


class EmailGrowthResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period: str
    kpis: list[MetricKpiDTO]
    time_series: list[MetricTimeSeriesDTO]
    sources: list[EmailSourcePerformanceDTO]
    retention_curve: list[EngagementDecayDTO]
