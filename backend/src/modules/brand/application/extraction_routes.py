"""Brand Studio route templates for copilot extraction cards.

SSoT for how extraction nav pills + summary CTAs route into the brand
studio editor. Lives in the brand module so changing brand routing
doesn't require editing copilot code (uniformity across modules).

The ``{tenantId}`` placeholder is left literal — the FE navigator
substitutes it at click-time from the current route. Never bake a
concrete tenant UUID here.
"""

from __future__ import annotations

NAV_ROUTE_TEMPLATE = "/{tenantId}/brand-studio/{section_slug}"


def primary_cta_route(sections_completed: list[str]) -> str | None:
    """Return the primary CTA route for the extraction summary card.

    Points to the first completed section. Returns None when no sections
    were completed (empty extraction run).
    """
    if not sections_completed:
        return None
    return f"/{{tenantId}}/brand-studio/{sections_completed[0]}"
