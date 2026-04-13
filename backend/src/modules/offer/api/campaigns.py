"""Offer campaigns view endpoint.

Aggregates KPIs + campaign rows scoped to a single offer using the
``AdvertisingReadPort``. ``offer`` never imports ``advertising`` directly
— the adapter is instantiated here and the returned DTO lives in
``shared/links/ports/advertising.py``.
"""

from datetime import date, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.advertising.application.services.offer_campaigns_read_adapter import (
    OfferCampaignsReadAdapter,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.shared.domain.datetime_utils import utc_now
from src.shared.links.ports.advertising import OfferCampaignsViewDTO

router = APIRouter()


_ALLOWED_STATUS = {"all", "active", "paused", "ended"}


def _resolve_period(period: str | None) -> tuple[date, date]:
    """Map a period shortcut to a ``(start, end)`` date range."""
    end = utc_now().date()
    days_by_period = {
        "7d": 7,
        "14d": 14,
        "30d": 30,
        "90d": 90,
    }
    days = days_by_period.get(period or "30d", 30)
    return end - timedelta(days=days), end


@router.get("/{offer_id}/campaigns")
async def get_offer_campaigns(
    offer_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    status: Annotated[str, Query()] = "all",
    channel: Annotated[str | None, Query()] = None,
    period: Annotated[str | None, Query()] = None,
) -> OfferCampaignsViewDTO:
    """Return aggregated campaigns for the given offer."""
    adapter = OfferCampaignsReadAdapter()
    normalized_status: Literal["all", "active", "paused", "ended"] = (
        status if status in _ALLOWED_STATUS else "all"  # type: ignore[assignment]
    )
    period_start, period_end = _resolve_period(period)
    return adapter.get_campaigns_for_offer(
        tenant_id=user.tenant_id,
        offer_id=UUID(offer_id),
        period_start=period_start,
        period_end=period_end,
        status=normalized_status,
        channel=channel,
    )
