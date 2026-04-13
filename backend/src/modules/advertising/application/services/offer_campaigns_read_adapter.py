"""Concrete ``AdvertisingReadPort`` for cross-module reads from ``offer``.

Stubbed for now — real aggregation over campaigns/ads filtered by
``offer_id`` is a follow-up once advertising exposes ``offer_id`` on its
campaign/ad tables. Returning an empty view keeps the UI contract stable
and lets the offer header render without hard-coupling to advertising
internals.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from src.shared.links.ports.advertising import (
    AdvertisingReadPort,
    CampaignAggregateKPIsDTO,
    OfferCampaignsViewDTO,
)

if TYPE_CHECKING:
    from datetime import date
    from uuid import UUID


class OfferCampaignsReadAdapter(AdvertisingReadPort):
    """Stub adapter that returns an empty campaigns view."""

    def get_campaigns_for_offer(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        *,
        period_start: date,
        period_end: date,
        status: Literal["all", "active", "paused", "ended"] = "all",
        channel: str | None = None,
    ) -> OfferCampaignsViewDTO:
        """Retrieve campaigns for offer."""
        # Stub: wire real aggregation when advertising
        # exposes offer_id on its campaign/ad tables.
        _ = (tenant_id, offer_id, period_start, period_end, status, channel)
        return OfferCampaignsViewDTO(
            kpis=CampaignAggregateKPIsDTO(
                active_count=0,
                spend_7d=0.0,
                leads_7d=0,
                avg_cpl_7d=None,
                currency=None,
            ),
            campaigns=[],
        )


__all__ = ["OfferCampaignsReadAdapter"]
