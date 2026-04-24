"""Offer Studio route templates for copilot extraction cards.

Offer routes need offer_id so users land on the editor of the specific
offer. NAV_ROUTE_TEMPLATE includes {entityId} placeholder, substituted
by the subscriber from event payload's entity_id.

The ``{tenantId}`` placeholder is left literal — the FE navigator
substitutes it at click-time from the current route. Never bake a
concrete tenant UUID here.

Route structure mirrors:
  app/(main)/[tenantId]/(dashboard)/offer-studio/offer/[id]/editor/[section]
"""

from __future__ import annotations

NAV_ROUTE_TEMPLATE = "/{tenantId}/offer-studio/offer/{entityId}/editor/{section_slug}"


def primary_cta_route(offer_id: str, sections_completed: list[str]) -> str | None:
    """Return the primary CTA route for the extraction summary card.

    Points to the first completed section of the specific offer.
    Returns None when no sections were completed (empty extraction run).
    """
    if not sections_completed:
        return None
    return f"/{{tenantId}}/offer-studio/offer/{offer_id}/editor/{sections_completed[0]}"
