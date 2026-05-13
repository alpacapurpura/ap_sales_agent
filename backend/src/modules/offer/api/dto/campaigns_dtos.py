"""Thin API-layer re-exports for ``GET /offers/{id}/campaigns``.

The actual shape lives in the shared advertising port so both ``offer``
and ``advertising`` agree on the contract without either importing the
other's internals.
"""

from __future__ import annotations

from luana_core_platform.links.ports.advertising import (
    CampaignAggregateKPIsDTO,
    CampaignRowDTO,
    OfferCampaignsViewDTO,
)

__all__ = [
    "CampaignAggregateKPIsDTO",
    "CampaignRowDTO",
    "OfferCampaignsViewDTO",
]
