"""Tests for HealthCheckService."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest

from src.modules.advertising.application.services.health_check_service import (
    HealthCheckService,
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


def _offer(
    tenant_id: UUID,
    *,
    name: str,
    archetype: str = "PROGRAMA",
    onboarding: str | None = None,
    checkout: str | None = None,
    is_lead_magnet: bool = False,
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
        checkout_page_url=checkout,
        landing_page_url=None,
        internal_sku=None,
        status="active",
    )


class TestHealthCheckService:
    @pytest.mark.asyncio
    async def test_empty_account_returns_healthy(self, db, tenant_id: UUID) -> None:
        port = _StubOfferReadPort([])
        svc = HealthCheckService(db, port)
        result = await svc.run(tenant_id)
        assert result.overall_status == "healthy"
        assert result.active_campaigns == []
        assert "No tenés campañas activas" in result.summary_text

    @pytest.mark.asyncio
    async def test_offer_without_campaign_yields_warning(
        self,
        db,
        tenant_id,
        make_offer,
    ) -> None:
        offer = _offer(tenant_id, name="Curso Estrella", checkout="https://x/y")
        port = _StubOfferReadPort([offer])
        svc = HealthCheckService(db, port)
        result = await svc.run(tenant_id)
        assert result.overall_status == "needs_attention"
        assert any(r.type == "create_campaign" for r in result.recommendations)
        assert any(not cov.has_active_campaign for cov in result.offers_coverage)

    @pytest.mark.asyncio
    async def test_unassigned_active_campaign_adds_info_recommendation(
        self,
        db,
        tenant_id,
        make_campaign,
    ) -> None:
        port = _StubOfferReadPort([])
        make_campaign(
            db,
            tenant_id=tenant_id,
            external_id="c1",
            name="Tráfico general",
            objective="OUTCOME_TRAFFIC",
            effective_status="ACTIVE",
        )
        svc = HealthCheckService(db, port)
        result = await svc.run(tenant_id)
        assert result.unassigned_targets, "should report unassigned target"
        assert any(r.type == "assign_offer" for r in result.recommendations)
        assert result.overall_status == "needs_attention"

    @pytest.mark.asyncio
    async def test_broken_expectation_sales_without_purchases(
        self,
        db,
        tenant_id,
        offer_id,
        make_campaign,
        make_metric,
    ) -> None:
        offer = _offer(
            tenant_id,
            name="Producto Digital",
            archetype="PRODUCTO",
            checkout="https://x/buy",
            offer_id=offer_id,
        )
        port = _StubOfferReadPort([offer])
        campaign = make_campaign(
            db,
            tenant_id=tenant_id,
            external_id="c1",
            name="Sales producto",
            objective="OUTCOME_SALES",
            effective_status="ACTIVE",
        )
        AssociationRepository(db).create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id=campaign.external_id,
            offer_id=offer_id,
            association_type=AssociationType.MANUAL,
        )
        # Spend metric exists but NO purchase events recorded:
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="spend",
            value=100.0,
            unit="currency",
            metric_date=date.today() - timedelta(days=1),
            campaign_id=campaign.external_id,
        )

        svc = HealthCheckService(db, port)
        result = await svc.run(tenant_id)
        assert result.overall_status == "critical"
        # Broken-expectation campaign flagged
        assert any(c.has_issue for c in result.active_campaigns)
        assert any(r.severity == "critical" for r in result.recommendations)

    @pytest.mark.asyncio
    async def test_excluded_branding_campaign_does_not_appear_as_unassigned(
        self,
        db,
        tenant_id,
        make_campaign,
    ) -> None:
        port = _StubOfferReadPort([])
        campaign = make_campaign(
            db,
            tenant_id=tenant_id,
            external_id="brand1",
            name="Awareness branding puro",
            objective="OUTCOME_AWARENESS",
            effective_status="ACTIVE",
        )
        AssociationRepository(db).create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id=campaign.external_id,
            offer_id=None,
            association_type=AssociationType.EXCLUDED_BRANDING,
        )
        svc = HealthCheckService(db, port)
        result = await svc.run(tenant_id)
        assert result.unassigned_targets == []
