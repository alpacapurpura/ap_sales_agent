"""Offer tab-bar counts aggregator.

Returns ``{assets, campaigns, knowledge}`` counts used by the header tab-bar
badges. Aggregates across three independent sources — assets (local repo),
knowledge (local repo), and campaigns (advertising module via
``AdvertisingReadPort``). Campaign port failures fall back to 0 so the
page never breaks when advertising integrations are down.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import structlog

from src.shared.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from uuid import UUID

    from src.modules.offer.application.ports import (
        IKnowledgeSourceRepository,
        IOfferAssetRepository,
    )
    from src.shared.links.ports.advertising import AdvertisingReadPort


logger = structlog.get_logger(__name__)


class OfferCountsService:
    """Service for offer counts operations."""

    def __init__(
        self,
        *,
        asset_repo: IOfferAssetRepository,
        knowledge_repo: IKnowledgeSourceRepository,
        advertising_port: AdvertisingReadPort,
    ) -> None:
        """Initialize service with dependencies."""
        self._asset_repo = asset_repo
        self._knowledge_repo = knowledge_repo
        self._advertising_port = advertising_port

    def get_counts(self, *, tenant_id: UUID, offer_id: UUID) -> dict[str, int]:
        """Retrieve counts."""
        assets = self._asset_repo.count_by_offer(tenant_id, offer_id)
        knowledge = self._knowledge_repo.count_by_offer(tenant_id, offer_id)
        campaigns = self._safe_campaign_count(tenant_id, offer_id)
        return {
            "assets": int(assets or 0),
            "campaigns": int(campaigns or 0),
            "knowledge": int(knowledge or 0),
        }

    def _safe_campaign_count(self, tenant_id: UUID, offer_id: UUID) -> int:
        end = utc_now().date()
        start = end - timedelta(days=30)
        try:
            view = self._advertising_port.get_campaigns_for_offer(
                tenant_id=tenant_id,
                offer_id=offer_id,
                period_start=start,
                period_end=end,
                status="all",
                channel=None,
            )
        except Exception:  # noqa: BLE001 — service resilience
            logger.warning(
                "offer_counts_advertising_fallback",
                offer_id=str(offer_id),
                tenant_id=str(tenant_id),
            )
            return 0
        campaigns = getattr(view, "campaigns", None) or []
        return len(campaigns)


__all__ = ["OfferCountsService"]
