"""Tests for OfferDetectionService."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from src.modules.advertising.application.services.offer_detection_service import (
    OfferDetectionService,
)
from src.modules.advertising.domain.enums import (
    AssociationTargetType,
    AssociationType,
)
from src.modules.advertising.infrastructure.repositories.association_repository import (
    AssociationRepository,
)
from src.shared.domain.ports import OfferReadDTO, OfferReadPort


class _StubOfferReadPort(OfferReadPort):
    def __init__(self, offers: list[OfferReadDTO]) -> None:
        self._offers = offers

    async def get_offers_by_tenant(self, tenant_id: UUID) -> list[OfferReadDTO]:
        return list(self._offers)

    async def get_offer_by_id(
        self,
        offer_id: UUID,
        tenant_id: UUID | None = None,
    ) -> OfferReadDTO | None:
        for o in self._offers:
            if o.id == offer_id:
                return o
        return None


def _make_offer(
    *,
    tenant_id: UUID,
    name: str,
    archetype: str = "PROGRAMA",
    landing_url: str | None = None,
    checkout_url: str | None = None,
    is_lead_magnet: bool = False,
    onboarding: str | None = None,
    offer_id: UUID | None = None,
) -> OfferReadDTO:
    return OfferReadDTO(
        id=offer_id or uuid4(),
        tenant_id=tenant_id,
        public_name=name,
        offer_type=archetype,
        value_level="TRANSFORMACION",
        pricing_type="one_time",
        currency="USD",
        is_lead_magnet=is_lead_magnet,
        onboarding_action=onboarding,
        checkout_page_url=checkout_url,
        landing_page_url=landing_url,
        internal_sku=None,
        status="active",
    )


class TestOfferDetectionService:
    @pytest.mark.asyncio
    async def test_empty_catalog_returns_empty_list(self, db, tenant_id: UUID) -> None:
        port = _StubOfferReadPort([])
        service = OfferDetectionService(db, port)
        result = await service.detect(tenant_id)
        assert result == []

    @pytest.mark.asyncio
    async def test_landing_url_match_suggests_ad_set_with_high_confidence(
        self,
        db,
        tenant_id,
        make_campaign,
        make_ad_set,
        make_ad,
    ) -> None:
        offer = _make_offer(
            tenant_id=tenant_id,
            name="MasterClass 2026",
            landing_url="https://visionarias.com/masterclass",
        )
        port = _StubOfferReadPort([offer])

        campaign = make_campaign(
            db,
            tenant_id=tenant_id,
            external_id="c1",
            name="Random Name",
        )
        ad_set = make_ad_set(
            db,
            tenant_id=tenant_id,
            external_id="as1",
            campaign_external_id=campaign.external_id,
            name="Audiencia fría",
        )
        make_ad(
            db,
            tenant_id=tenant_id,
            external_id="ad1",
            campaign_external_id=campaign.external_id,
            ad_set_external_id=ad_set.external_id,
            name="video-1",
            creative_link_url="https://www.visionarias.com/masterclass?utm=fb",
        )

        service = OfferDetectionService(db, port)
        result = await service.detect(tenant_id)

        ad_set_hits = [s for s in result if s.target_type == "ad_set"]
        assert len(ad_set_hits) == 1
        hit = ad_set_hits[0]
        assert hit.target_external_id == "as1"
        assert hit.confidence == "high"
        assert hit.association_type == "auto_landing_url"
        assert hit.suggested_offer_id == offer.id

    @pytest.mark.asyncio
    async def test_keyword_match_at_campaign_level_medium_confidence(
        self,
        db,
        tenant_id,
        make_campaign,
    ) -> None:
        offer = _make_offer(tenant_id=tenant_id, name="Curso Marketing Digital")
        port = _StubOfferReadPort([offer])

        make_campaign(
            db,
            tenant_id=tenant_id,
            external_id="c1",
            name="Ventas - Curso Marketing Digital 2026",
            objective="OUTCOME_SALES",
        )

        service = OfferDetectionService(db, port)
        result = await service.detect(tenant_id)
        campaign_hits = [s for s in result if s.target_type == "campaign"]
        assert len(campaign_hits) == 1
        hit = campaign_hits[0]
        assert hit.confidence == "medium"
        assert hit.association_type == "auto_keyword"
        assert hit.suggested_offer_id == offer.id

    @pytest.mark.asyncio
    async def test_existing_association_is_skipped(
        self,
        db,
        tenant_id,
        offer_id,
        make_campaign,
    ) -> None:
        offer = _make_offer(
            tenant_id=tenant_id,
            name="Curso Marketing Digital",
            offer_id=offer_id,
        )
        port = _StubOfferReadPort([offer])

        make_campaign(
            db,
            tenant_id=tenant_id,
            external_id="c1",
            name="Ventas Curso Marketing Digital",
        )
        AssociationRepository(db).create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id="c1",
            offer_id=offer_id,
            association_type=AssociationType.MANUAL,
        )

        service = OfferDetectionService(db, port)
        result = await service.detect(tenant_id)
        assert result == []  # already assigned, no suggestions

    @pytest.mark.asyncio
    async def test_objective_heuristic_only_fires_with_unique_match(
        self,
        db,
        tenant_id,
        make_campaign,
    ) -> None:
        # One SERVICIO offer with no explicit onboarding → resolves to MESSAGE.
        # The campaign has OUTCOME_MESSAGES → expected=MESSAGE → single match.
        offer = _make_offer(
            tenant_id=tenant_id,
            name="Totalmente Distinto",
            archetype="SERVICIO",
            onboarding=None,
        )
        port = _StubOfferReadPort([offer])

        make_campaign(
            db,
            tenant_id=tenant_id,
            external_id="c1",
            name="Branding awareness spring",
            objective="OUTCOME_MESSAGES",
        )

        service = OfferDetectionService(db, port)
        result = await service.detect(tenant_id)
        assert len(result) == 1
        hit = result[0]
        assert hit.association_type == "auto_objective"
        assert hit.confidence == "low"

    @pytest.mark.asyncio
    async def test_archived_offers_are_excluded(
        self,
        db,
        tenant_id,
        make_campaign,
    ) -> None:
        offer = _make_offer(
            tenant_id=tenant_id,
            name="Archivada Curso Marketing Digital",
        )
        offer.status = "archived"  # type: ignore[misc]
        port = _StubOfferReadPort([offer])
        make_campaign(
            db,
            tenant_id=tenant_id,
            external_id="c1",
            name="Curso Marketing Digital Promo",
        )
        service = OfferDetectionService(db, port)
        assert await service.detect(tenant_id) == []
