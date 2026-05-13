"""Cross-module read ports.

These live under ``shared.links.ports`` so that consumer modules (e.g.
``offer``) can aggregate data owned by other modules (e.g. ``advertising``)
without ever importing from those modules directly.

The concrete adapter is owned by the provider module and wired at startup
via FastAPI ``Depends``. The consumer only knows the port.
"""

from luana_core_platform.links.ports.advertising import (
    AdvertisingReadPort,
    CampaignAggregateKPIsDTO,
    CampaignRowDTO,
    OfferCampaignsViewDTO,
)

__all__ = [
    "AdvertisingReadPort",
    "CampaignAggregateKPIsDTO",
    "CampaignRowDTO",
    "OfferCampaignsViewDTO",
]
