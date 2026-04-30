"""Cross-module read port for campaigns.

Consumed by copilot subagent (PI-2) and CRM Hub (S4).
Exposes service factories without leaking internals.
DDD: never import from modules/campaigns directly — use this port.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession


class CampaignReadOnlyPort(Protocol):
    """Read-only view of campaigns for cross-module consumers."""

    async def get_campaign_summary(
        self,
        *,
        tenant_id: UUID,
        campaign_id: UUID,
        session: AsyncSession,
    ) -> dict | None:
        """Return dict shape compatible with CampaignResponse fields (read-only).

        Decouples consumers from domain entity churn.
        Returns None if campaign not found or not owned by tenant.
        """


def get_campaign_read_port() -> CampaignReadOnlyPort:
    """Lazy factory. PI-2 commercial_director subagent consumes via this."""
    from src.modules.campaigns.application.services.campaign_read_adapter import (
        CampaignReadAdapter,
    )

    return CampaignReadAdapter()
