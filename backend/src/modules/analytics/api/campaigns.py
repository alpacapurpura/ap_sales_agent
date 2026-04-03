"""Campaign management API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.analytics.application.dto.campaign_dto import (
    AdDTO,
    AdSetDTO,
    CampaignOverviewDTO,
)
from src.modules.analytics.application.services.campaign_service import (
    CampaignService,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

router = APIRouter(prefix="/campaigns", tags=["Analytics - Campaigns"])


@router.get("", response_model=CampaignOverviewDTO)
async def get_campaigns_overview(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = CampaignService(db)
    return service.get_overview(user.tenant_id)


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


@router.post("/sync")
async def trigger_campaign_sync(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = CampaignService(db)
    return await service.trigger_sync(user.tenant_id)
