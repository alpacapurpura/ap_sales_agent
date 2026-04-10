"""Tests for CampaignTemplateService."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from src.modules.advertising.application.services.campaign_template_service import (
    CampaignTemplateService,
)
from src.modules.advertising.infrastructure.models.ad_campaign_template_model import (
    AdCampaignTemplateModel,
)
from src.shared.domain.ports import OfferReadDTO, OfferReadPort


class _StubOfferReadPort(OfferReadPort):
    def __init__(self, offers: list[OfferReadDTO]) -> None:
        self._offers = offers

    async def get_offers_by_tenant(self, tenant_id: UUID) -> list[OfferReadDTO]:
        return list(self._offers)

    async def get_offer_by_id(
        self, offer_id: UUID, tenant_id: UUID | None = None
    ) -> OfferReadDTO | None:
        for o in self._offers:
            if o.id == offer_id:
                return o
        return None


def _seed_minimal_templates(db) -> None:
    db.add(
        AdCampaignTemplateModel(
            id=uuid4(),
            offer_archetype="PROGRAMA",
            offer_onboarding_action=None,
            offer_is_lead_magnet=False,
            name="Programa - Checkout directo",
            description="Programa con checkout directo",
            recommended_objective="OUTCOME_SALES",
            priority=100,
        )
    )
    db.add(
        AdCampaignTemplateModel(
            id=uuid4(),
            offer_archetype="SERVICIO",
            offer_onboarding_action="BOOK_KICKOFF_CALL",
            offer_is_lead_magnet=False,
            name="Servicio - Mensajes para agendar",
            description="Servicio 1:1 via DMs",
            recommended_objective="OUTCOME_MESSAGES",
            priority=100,
        )
    )
    db.flush()


class TestCampaignTemplateService:
    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_offer(self, db, tenant_id):
        port = _StubOfferReadPort([])
        svc = CampaignTemplateService(db, port)
        result = await svc.get_template_for_offer(tenant_id, uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_matches_servicio_with_book_call(self, db, tenant_id):
        _seed_minimal_templates(db)
        offer = OfferReadDTO(
            id=uuid4(),
            tenant_id=tenant_id,
            public_name="Asesoría 1:1",
            offer_type="SERVICIO",
            value_level="MAXIMIZACION",
            pricing_type="one_time",
            currency="USD",
            is_lead_magnet=False,
            onboarding_action="BOOK_KICKOFF_CALL",
            checkout_page_url=None,
            landing_page_url=None,
            internal_sku=None,
            status="active",
        )
        port = _StubOfferReadPort([offer])
        svc = CampaignTemplateService(db, port)
        result = await svc.get_template_for_offer(tenant_id, offer.id)
        assert result is not None
        assert result.offer_archetype == "SERVICIO"
        assert result.recommended_objective == "OUTCOME_MESSAGES"
        assert "Mensajes" in result.recommended_objective_label_es

    @pytest.mark.asyncio
    async def test_matches_programa_fallback(self, db, tenant_id):
        _seed_minimal_templates(db)
        offer = OfferReadDTO(
            id=uuid4(),
            tenant_id=tenant_id,
            public_name="Curso online",
            offer_type="PROGRAMA",
            value_level="TRANSFORMACION",
            pricing_type="one_time",
            currency="USD",
            is_lead_magnet=False,
            onboarding_action=None,
            checkout_page_url="https://buy/curso",
            landing_page_url=None,
            internal_sku=None,
            status="active",
        )
        port = _StubOfferReadPort([offer])
        svc = CampaignTemplateService(db, port)
        result = await svc.get_template_for_offer(tenant_id, offer.id)
        assert result is not None
        assert result.offer_archetype == "PROGRAMA"
        assert result.recommended_objective == "OUTCOME_SALES"

    @pytest.mark.asyncio
    async def test_no_template_for_unknown_archetype(self, db, tenant_id):
        _seed_minimal_templates(db)
        offer = OfferReadDTO(
            id=uuid4(),
            tenant_id=tenant_id,
            public_name="Rare",
            offer_type="EXPERIENCIA_RARA",
            value_level="TRANSFORMACION",
            pricing_type="one_time",
            currency="USD",
            is_lead_magnet=False,
            onboarding_action=None,
            checkout_page_url=None,
            landing_page_url=None,
            internal_sku=None,
            status="active",
        )
        port = _StubOfferReadPort([offer])
        svc = CampaignTemplateService(db, port)
        result = await svc.get_template_for_offer(tenant_id, offer.id)
        assert result is None
