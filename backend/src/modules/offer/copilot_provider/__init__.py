"""Offer module — copilot provider entry point.

F1 ships a shim: ``module_data()`` is lifted from the legacy registry and the
real tool migration (offer_section_tools + offer_ladder_tools, 19 tools) is a
follow-up. The provider is discoverable today so registry refactors can rely
on every module having one.

[COPILOT-PROVIDER-PATTERN]
"""

from __future__ import annotations

from src.modules.offer.copilot_provider.provider import OfferCopilotProvider

provider: OfferCopilotProvider = OfferCopilotProvider()

__all__ = ("OfferCopilotProvider", "provider")
