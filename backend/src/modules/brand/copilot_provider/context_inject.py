"""Brand context injector — placeholder until F3.

F3 wires this to ``brand_summary`` so every system prompt receives a stable
≤800-char "lighthouse" of the tenant's brand without paying the round trip
to fetch raw fields. F1 keeps the contract surface only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


class BrandContextInjector:
    """Returns a per-route system-prompt fragment (F3 will populate)."""

    async def inject_for(self, *, target_route: str, tenant_id: UUID) -> str | None:
        _ = (target_route, tenant_id)
        return None
