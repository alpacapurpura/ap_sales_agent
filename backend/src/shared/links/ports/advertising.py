"""AdvertisingReadPort — cross-module read port for campaign aggregation.

``offer`` uses this to render the Campañas tab without importing from the
``advertising`` module. The concrete adapter lives in
``advertising/application/services/offer_campaigns_read_adapter.py``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from datetime import date


class CampaignRowDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    channel: str  # "meta" | "google" | "tiktok" | ...
    status: str  # "active" | "paused" | "ended"
    spend: float
    leads: int
    cpl: float | None = None
    currency: str | None = None  # per-row currency (source of truth)


class CampaignAggregateKPIsDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    active_count: int
    spend_7d: float
    leads_7d: int
    avg_cpl_7d: float | None = None
    currency: str | None = None


class OfferCampaignsViewDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    kpis: CampaignAggregateKPIsDTO
    campaigns: list[CampaignRowDTO]


class AdvertisingReadPort(ABC):
    """Read-only port so ``offer`` can aggregate campaigns without importing
    any ``advertising`` internals.

    Implementations live in the advertising module and are wired via
    FastAPI ``Depends`` at the route level.
    """

    @abstractmethod
    def get_campaigns_for_offer(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        *,
        period_start: date,
        period_end: date,
        status: Literal["all", "active", "paused", "ended"] = "all",
        channel: str | None = None,
    ) -> OfferCampaignsViewDTO: ...


__all__ = [
    "AdvertisingReadPort",
    "CampaignAggregateKPIsDTO",
    "CampaignRowDTO",
    "OfferCampaignsViewDTO",
]
