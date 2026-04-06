"""Campaign management API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.analytics.application.dto.campaign_dto import (
    AdDTO,
    AdSetDTO,
    CampaignOverviewDTO,
    CampaignPerformanceDTO,
    CreativesOverviewDTO,
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


router = APIRouter(prefix="/campaigns", tags=["Analytics - Campaigns"])


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
    valid_periods = {"7d", "30d", "90d"}
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period: {period}. Must be one of {valid_periods}",
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
    valid_periods = {"7d", "30d", "90d"}
    if period not in valid_periods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period: {period}. Must be one of {valid_periods}",
        )
    service = CampaignService(db)
    return service.get_creatives_overview(user.tenant_id, period)


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


@router.post("/sync", response_model=CampaignSyncResponse)
async def trigger_campaign_sync(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = CampaignService(db)
    return await service.trigger_sync(user.tenant_id)
