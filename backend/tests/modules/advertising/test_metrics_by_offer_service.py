"""Tests for MetricsByOfferService."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from src.modules.advertising.application.services.metrics_by_offer_service import (
    MetricsByOfferService,
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
        self, offer_id: UUID, tenant_id: UUID | None = None
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
        is_lead_magnet=False,
        onboarding_action=onboarding,
        checkout_page_url=checkout,
        landing_page_url=None,
        internal_sku=None,
        status="active",
    )


class TestMetricsByOfferService:
    @pytest.mark.asyncio
    async def test_purchase_offer_computes_roas_and_cost_per_purchase(
        self, db, tenant_id, offer_id, make_offer, make_campaign, make_metric
    ) -> None:
        offer = _offer(
            tenant_id,
            name="Curso",
            archetype="PROGRAMA",
            checkout="https://buy/curso",
            offer_id=offer_id,
        )
        port = _StubOfferReadPort([offer])

        campaign = make_campaign(
            db, tenant_id=tenant_id, external_id="c1", name="Sales"
        )
        AssociationRepository(db).create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id=campaign.external_id,
            offer_id=offer_id,
            association_type=AssociationType.MANUAL,
        )
        today = date.today()
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="spend",
            value=100.0,
            unit="currency",
            metric_date=today,
            campaign_id=campaign.external_id,
        )
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="conversions",
            value=4.0,
            unit="count",
            metric_date=today,
            campaign_id=campaign.external_id,
        )
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="meta_conversion_value",
            value=250.0,
            unit="currency",
            metric_date=today,
            campaign_id=campaign.external_id,
        )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id, period="30d")
        assert len(result.offers) == 1
        off = result.offers[0]
        assert off.total_spend == 100.0
        assert off.primary_result_count == 4.0
        assert off.primary_cost_per_result == 25.0
        assert off.roas == 2.5
        assert off.expected_metric == "purchase"

    @pytest.mark.asyncio
    async def test_message_offer_uses_conversations_metric(
        self, db, tenant_id, offer_id, make_campaign, make_metric
    ) -> None:
        offer = _offer(
            tenant_id,
            name="Asesoría",
            archetype="SERVICIO",
            onboarding=None,
            offer_id=offer_id,
        )
        port = _StubOfferReadPort([offer])
        campaign = make_campaign(
            db, tenant_id=tenant_id, external_id="c1", name="Messages"
        )
        AssociationRepository(db).create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id=campaign.external_id,
            offer_id=offer_id,
            association_type=AssociationType.MANUAL,
        )
        today = date.today()
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="spend",
            value=60.0,
            unit="currency",
            metric_date=today,
            campaign_id=campaign.external_id,
        )
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="meta_conversations_started",
            value=12.0,
            unit="count",
            metric_date=today,
            campaign_id=campaign.external_id,
        )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id)
        assert len(result.offers) == 1
        off = result.offers[0]
        assert off.expected_metric == "message"
        assert off.primary_result_count == 12.0
        assert off.primary_cost_per_result == 5.0
        assert off.roas is None

    @pytest.mark.asyncio
    async def test_unassigned_spend_goes_into_unassigned_bucket(
        self, db, tenant_id, make_campaign, make_metric
    ) -> None:
        port = _StubOfferReadPort([])
        campaign = make_campaign(
            db, tenant_id=tenant_id, external_id="c1", name="Sin asignar"
        )
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="spend",
            value=75.0,
            unit="currency",
            metric_date=date.today(),
            campaign_id=campaign.external_id,
        )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id)
        assert result.unassigned.total_spend == 75.0
        assert result.unassigned.target_count >= 1
        assert result.offers == []

    @pytest.mark.asyncio
    async def test_branding_exclusion_routes_spend_to_branding_bucket(
        self, db, tenant_id, make_campaign, make_metric
    ) -> None:
        port = _StubOfferReadPort([])
        campaign = make_campaign(
            db, tenant_id=tenant_id, external_id="br1", name="Brand awareness"
        )
        AssociationRepository(db).create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id=campaign.external_id,
            offer_id=None,
            association_type=AssociationType.EXCLUDED_BRANDING,
        )
        today = date.today()
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="spend",
            value=200.0,
            unit="currency",
            metric_date=today,
            campaign_id=campaign.external_id,
        )
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="reach",
            value=15000.0,
            unit="count",
            metric_date=today,
            campaign_id=campaign.external_id,
        )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id)
        assert result.branding_only.total_spend == 200.0
        assert result.branding_only.reach == 15000.0
        assert result.unassigned.total_spend == 0.0

    @pytest.mark.asyncio
    async def test_no_events_reported_sets_unavailable_reason(
        self, db, tenant_id, offer_id, make_campaign, make_metric
    ) -> None:
        offer = _offer(
            tenant_id,
            name="Curso",
            archetype="PROGRAMA",
            checkout="https://buy/curso",
            offer_id=offer_id,
        )
        port = _StubOfferReadPort([offer])
        campaign = make_campaign(
            db, tenant_id=tenant_id, external_id="c1", name="Sales curso"
        )
        AssociationRepository(db).create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id=campaign.external_id,
            offer_id=offer_id,
            association_type=AssociationType.MANUAL,
        )
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="spend",
            value=80.0,
            unit="currency",
            metric_date=date.today(),
            campaign_id=campaign.external_id,
        )
        # No purchase metrics recorded.

        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id)
        off = result.offers[0]
        assert off.primary_cost_per_result is None
        assert off.metric_unavailable_reason == "no_events_reported"
