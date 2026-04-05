"""DTOs for campaign management API responses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


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
