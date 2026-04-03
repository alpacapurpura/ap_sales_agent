"""DTOs for campaign management API responses."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CampaignDTO(BaseModel):
    external_id: str
    name: str
    objective: Optional[str] = None
    status: Optional[str] = None
    effective_status: Optional[str] = None
    bid_strategy: Optional[str] = None
    daily_budget: Optional[int] = None
    lifetime_budget: Optional[int] = None
    budget_remaining: Optional[int] = None
    buying_type: Optional[str] = None
    start_time: Optional[datetime] = None
    stop_time: Optional[datetime] = None
    ad_sets_count: int = 0
    ads_count: int = 0


class AdSetDTO(BaseModel):
    external_id: str
    campaign_external_id: str
    name: str
    status: Optional[str] = None
    effective_status: Optional[str] = None
    optimization_goal: Optional[str] = None
    targeting_summary: Optional[dict] = None
    learning_stage: Optional[str] = None
    daily_budget: Optional[int] = None
    ads_count: int = 0


class AdDTO(BaseModel):
    external_id: str
    name: str
    status: Optional[str] = None
    effective_status: Optional[str] = None
    creative_thumbnail_url: Optional[str] = None
    creative_title: Optional[str] = None
    creative_cta: Optional[str] = None
    preview_shareable_link: Optional[str] = None


class RecommendationDTO(BaseModel):
    recommendation_type: str
    source: str
    title: Optional[str] = None
    body: Optional[str] = None
    importance: Optional[str] = None
    lift_estimate: Optional[str] = None
    opportunity_score: Optional[float] = None
    url: Optional[str] = None
    object_ids: list = []


class CampaignOverviewDTO(BaseModel):
    campaigns: list[CampaignDTO]
    recommendations: list[RecommendationDTO]
    total_campaigns: int
    active_campaigns: int
    last_synced: Optional[datetime] = None
