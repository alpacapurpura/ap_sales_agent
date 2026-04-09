"""API endpoints for the Email Intelligence Hub dashboard."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query

from src.core.database import get_db
from src.modules.analytics.application.dto.email_dashboard_dto import (
    EmailAudienceResponseDTO,
    EmailAutomationsResponseDTO,
    EmailCampaignsResponseDTO,
    EmailDashboardDTO,
    EmailGrowthResponseDTO,
    EmailHealthResponseDTO,
)
from src.modules.analytics.application.services.email_dashboard_service import (
    EmailDashboardService,
)
from src.modules.iam.api.dependencies import get_current_user

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.modules.iam.domain.user import User

router = APIRouter(prefix="/email", tags=["email-dashboard"])


@router.get("/dashboard", response_model=EmailDashboardDTO)
async def get_email_dashboard(
    period: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailDashboardDTO:
    """Main sidebar + Panorama tab data for Email Intelligence Hub."""
    service = EmailDashboardService(db)
    return await service.get_dashboard(user.tenant_id, period)


@router.get("/campaigns", response_model=EmailCampaignsResponseDTO)
async def get_email_campaigns(
    period: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailCampaignsResponseDTO:
    """Campaign analysis: type breakdown, campaign list, top subjects."""
    service = EmailDashboardService(db)
    return await service.get_campaigns(user.tenant_id, period)


@router.get("/automations", response_model=EmailAutomationsResponseDTO)
async def get_email_automations(
    period: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailAutomationsResponseDTO:
    """Automation performance data."""
    service = EmailDashboardService(db)
    return await service.get_automations(user.tenant_id, period)


@router.get("/audience", response_model=EmailAudienceResponseDTO)
async def get_email_audience(
    period: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailAudienceResponseDTO:
    """Audience engagement segmentation, decay, and heatmap."""
    service = EmailDashboardService(db)
    return await service.get_audience(user.tenant_id, period)


@router.get("/health", response_model=EmailHealthResponseDTO)
async def get_email_health(
    period: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailHealthResponseDTO:
    """Deliverability health: bounce breakdown, alerts, score."""
    service = EmailDashboardService(db)
    return await service.get_health(user.tenant_id, period)


@router.get("/growth", response_model=EmailGrowthResponseDTO)
async def get_email_growth(
    period: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailGrowthResponseDTO:
    """List growth: subscribers, churn, sources, retention."""
    service = EmailDashboardService(db)
    return await service.get_growth(user.tenant_id, period)
