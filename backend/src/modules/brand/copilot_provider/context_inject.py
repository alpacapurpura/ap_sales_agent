"""Brand context injector — F3 lighthouse system-prompt fragment.

# [COPILOT-BRAND-SUMMARY-F3] -> docs/domains/copilot/redesign-2026-04/phases/F3-brand-summary-lighthouse.md

When ``target_route`` matches one of the surfaces where brand
coherence matters most (offer/landing/campaign/sales) we surface the
≤800-char living summary as a stable prompt prefix the LLM can rely on
without paying the round trip to fetch raw fields. ``None`` everywhere
else — Brand Studio itself doesn't need the lighthouse since the user
is editing the source.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from luana_core_brand_studio.copilot_provider.summary import BrandSummaryProvider

if TYPE_CHECKING:
    from uuid import UUID


# Route SEGMENT allowlist. ``current_route`` arrives as ``/{tenantId}/...``
# so we match on substring presence rather than exact prefix to remain
# resilient to nested paths (``offer-studio/offer/<id>``,
# ``sales/studio/inbox``…). ``brand-studio`` is intentionally absent —
# users editing brand data don't need the distilled view of their own
# input back at them.
_INJECTION_SEGMENTS: tuple[str, ...] = (
    "offer-studio",
    "landing",
    "campaign",
    "sales",
    "growth-studio",
)


def _route_in_allowlist(route: str | None) -> bool:
    if not route:
        return False
    needle = route.lower()
    return any(seg in needle for seg in _INJECTION_SEGMENTS)


class BrandContextInjector:
    """Returns a per-route system-prompt fragment (F3 lighthouse)."""

    INJECTION_SEGMENTS: tuple[str, ...] = _INJECTION_SEGMENTS

    def __init__(self, summary_provider: BrandSummaryProvider | None = None) -> None:
        """Bind the summary provider — defaults to the canonical brand impl."""
        self._summary_provider = summary_provider or BrandSummaryProvider()

    async def inject_for(self, *, target_route: str, tenant_id: UUID) -> str | None:
        """Return the lighthouse fragment when ``target_route`` matches.

        ``None`` when the route is off-allowlist or the tenant has no
        persisted summary yet. Caller (system prompt builder) treats
        ``None`` as "skip", so unaffected routes pay no extra latency.
        """
        if not _route_in_allowlist(target_route):
            return None
        summary = await self._summary_provider.summary(tenant_id=tenant_id)
        if not summary:
            return None
        return (
            "## Brand Lighthouse\n"
            f"{summary}\n\n"
            "Toma decisiones desde aquí. Si algo es incoherente con la marca, "
            "dilo antes de proponer."
        )
