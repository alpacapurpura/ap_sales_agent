"""Campaign management API routes."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.analytics.application.dto.campaign_dto import (
    AdDTO,
    AdPerformanceListDTO,
    AdSetDTO,
    CampaignOverviewDTO,
    CampaignPerformanceDTO,
    CreativesOverviewDTO,
    FormatComparisonDTO,
)
from src.modules.analytics.application.services.ad_performance_service import (
    AdPerformanceService,
)
from src.modules.analytics.application.services.campaign_service import (
    CampaignService,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User


class CampaignSyncResponse(BaseModel):
    """Response for campaign sync trigger."""

    status: str
    job_id: str | None = None


class CampaignSyncStatusDTO(BaseModel):
    """Status of the last campaign sync job."""

    status: str
    campaigns_synced: int | None = None
    ad_sets_synced: int | None = None
    ads_synced: int | None = None
    recommendations_synced: int | None = None


router = APIRouter(prefix="/campaigns", tags=["Analytics - Campaigns"])

_VALID_PERIODS = {"7d", "30d", "90d"}


@router.get("", response_model=CampaignOverviewDTO)
async def get_campaigns_overview(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = CampaignService(db)
    return service.get_overview(user.tenant_id)


@router.get("/performance", response_model=CampaignPerformanceDTO)
async def get_campaigns_performance(
    period: str = Query(default="30d"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all campaigns with aggregated performance metrics."""
    if period not in _VALID_PERIODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period: {period}. Must be one of {_VALID_PERIODS}",
        )
    service = CampaignService(db)
    return service.get_performance(user.tenant_id, period)


@router.get("/creatives", response_model=CreativesOverviewDTO)
async def get_creatives_overview(
    period: str = Query(default="30d"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get ad gallery with creative details and video retention metrics.

    Returns all ads with campaign names, creative thumbnails, and
    aggregated video retention funnel metrics for the given period.
    """
    if period not in _VALID_PERIODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period: {period}. Must be one of {_VALID_PERIODS}",
        )
    service = CampaignService(db)
    return service.get_creatives_overview(user.tenant_id, period)


@router.get("/ads/performance", response_model=AdPerformanceListDTO)
async def get_ads_performance(
    period: str = Query(default="30d"),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get top ads with per-ad performance metrics (ROAS, CPA, CTR, CPC)."""
    if period not in _VALID_PERIODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period: {period}. Must be one of {_VALID_PERIODS}",
        )
    service = AdPerformanceService(db)
    return service.get_top_ads(user.tenant_id, "meta-ads", period, limit)


@router.get("/ads/format-comparison", response_model=FormatComparisonDTO)
async def get_ads_format_comparison(
    period: str = Query(default="30d"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get aggregated metrics by ad format (video, carousel, image)."""
    if period not in _VALID_PERIODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period: {period}. Must be one of {_VALID_PERIODS}",
        )
    service = AdPerformanceService(db)
    return service.get_format_comparison(user.tenant_id, "meta-ads", period)


@router.get("/{campaign_external_id}/adsets", response_model=list[AdSetDTO])
async def get_campaign_ad_sets(
    campaign_external_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = CampaignService(db)
    return service.get_ad_sets(user.tenant_id, campaign_external_id)


@router.get("/adsets/{ad_set_external_id}/ads", response_model=list[AdDTO])
async def get_ad_set_ads(
    ad_set_external_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = CampaignService(db)
    return service.get_ads(user.tenant_id, ad_set_external_id)


@router.get("/sync/status", response_model=CampaignSyncStatusDTO)
async def get_campaign_sync_status(
    user: User = Depends(get_current_user),
):
    """Get the status of the last campaign sync job for this tenant."""
    from src.core.database import redis_client

    if not redis_client:
        return CampaignSyncStatusDTO(status="unknown")

    key = f"campaign_sync:{user.tenant_id}:meta"
    raw = redis_client.get(key)
    if not raw:
        return CampaignSyncStatusDTO(status="never_synced")

    data = json.loads(raw)
    return CampaignSyncStatusDTO(
        status=data.get("status", "unknown"),
        campaigns_synced=data.get("campaigns_synced"),
        ad_sets_synced=data.get("ad_sets_synced"),
        ads_synced=data.get("ads_synced"),
        recommendations_synced=data.get("recommendations_synced"),
    )


@router.post("/sync", response_model=CampaignSyncResponse)
async def trigger_campaign_sync(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = CampaignService(db)
    return await service.trigger_sync(user.tenant_id)
