"""Brand summary provider — placeholder until F3 wires the lighthouse.

F3 (``phases/F3-brand-summary-lighthouse.md``) introduces a ``brand_summary``
table populated by an ARQ task on ``BrandSectionUpdated`` events. Until then
``summary()`` returns ``None`` and the system prompt falls back to the legacy
brand snippet built from raw fields.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID


class BrandSummaryProvider:
    """Returns a ≤800-char living brand summary (F3 will populate)."""

    async def summary(self, *, tenant_id: UUID) -> str | None:
        _ = tenant_id  # acknowledged for protocol compatibility
        return None
