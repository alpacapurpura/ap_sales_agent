"""API endpoints for the Email Intelligence Hub dashboard."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

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
from src.modules.iam.domain.user import User

router = APIRouter(prefix="/email", tags=["email-dashboard"])


@router.get("/dashboard")
async def get_email_dashboard(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    period: Annotated[str, Query(pattern="^(7d|30d|90d)$")] = "30d",
) -> EmailDashboardDTO:
    """Return main sidebar and Panorama tab data for Email Intelligence Hub."""
    service = EmailDashboardService(db)
    return await service.get_dashboard(user.tenant_id, period)


@router.get("/campaigns")
async def get_email_campaigns(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    period: Annotated[str, Query(pattern="^(7d|30d|90d)$")] = "30d",
) -> EmailCampaignsResponseDTO:
    """Campaign analysis: type breakdown, campaign list, top subjects."""
    service = EmailDashboardService(db)
    return await service.get_campaigns(user.tenant_id, period)


@router.get("/automations")
async def get_email_automations(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    period: Annotated[str, Query(pattern="^(7d|30d|90d)$")] = "30d",
) -> EmailAutomationsResponseDTO:
    """Automation performance data."""
    service = EmailDashboardService(db)
    return await service.get_automations(user.tenant_id, period)


@router.get("/audience")
async def get_email_audience(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    period: Annotated[str, Query(pattern="^(7d|30d|90d)$")] = "30d",
) -> EmailAudienceResponseDTO:
    """Audience engagement segmentation, decay, and heatmap."""
    service = EmailDashboardService(db)
    return await service.get_audience(user.tenant_id, period)


@router.get("/health")
async def get_email_health(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    period: Annotated[str, Query(pattern="^(7d|30d|90d)$")] = "30d",
) -> EmailHealthResponseDTO:
    """Deliverability health: bounce breakdown, alerts, score."""
    service = EmailDashboardService(db)
    return await service.get_health(user.tenant_id, period)


@router.get("/growth")
async def get_email_growth(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    period: Annotated[str, Query(pattern="^(7d|30d|90d)$")] = "30d",
) -> EmailGrowthResponseDTO:
    """List growth: subscribers, churn, sources, retention."""
    service = EmailDashboardService(db)
    return await service.get_growth(user.tenant_id, period)
