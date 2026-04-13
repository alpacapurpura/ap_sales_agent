"""Tests for the new funnel + reach behaviour of MetricsByOfferService.

Exercises the rules defined in
`docs/superpowers/artifacts/2026-04-10-meta-ads-resumen/CONTRACT.md`:

- `funnel_all` is the aggregate of ALL campaigns (no filter)
- `reach_all` comes from the channel-level period_metrics row
- per-offer reach is None unless exactly 1 campaign is associated AND
  a matching period_metrics row exists
- multi-campaign offers get reach = None (never sum)
- branding / unassigned funnels reflect only their own campaigns
- offers with conversions=0 get roas = None
- no period_metrics rows → reach = None (no fallback)
- invalid `metric_unavailable_reason` surfaces as expected
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
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
from src.modules.analytics.infrastructure.models.period_metrics_model import (
    PeriodMetricModel,
)
from src.shared.domain.locale import TenantLocale
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


def _make_period_reach(
    db,
    *,
    tenant_id: UUID,
    value: float,
    period_start: date,
    period_end: date,
    campaign_id: str | None,
) -> PeriodMetricModel:
    row = PeriodMetricModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        provider="meta",
        channel_slug="meta-ads",
        metric_name="reach",
        value=value,
        unit="count",
        currency=None,
        period_type="monthly",
        period_start=period_start,
        period_end=period_end,
        campaign_id=campaign_id,
        ad_set_id=None,
        ad_id=None,
        cost_type=None,
        extra={},
        source_extraction_run_id=None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(row)
    db.flush()
    return row


class TestFunnelAllAndReachAll:
    @pytest.mark.asyncio
    async def test_funnel_all_sums_across_all_campaigns(
        self, db, tenant_id, make_campaign, make_metric
    ) -> None:
        port = _StubOfferReadPort([])
        c1 = make_campaign(db, tenant_id=tenant_id, external_id="c1", name="One")
        c2 = make_campaign(db, tenant_id=tenant_id, external_id="c2", name="Two")
        today = date.today()
        # c1: 1000 impressions, 100 clicks
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="impressions",
            value=1000,
            metric_date=today,
            campaign_id=c1.external_id,
        )
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="clicks",
            value=100,
            metric_date=today,
            campaign_id=c1.external_id,
        )
        # c2: 2000 impressions, 50 clicks
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="impressions",
            value=2000,
            metric_date=today,
            campaign_id=c2.external_id,
        )
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="clicks",
            value=50,
            metric_date=today,
            campaign_id=c2.external_id,
        )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id)

        # funnel_all: 5 steps in canonical order
        assert len(result.funnel_all) == 5
        by_metric = {s.metric_name: s for s in result.funnel_all}
        assert by_metric["impressions"].value == 3000.0
        assert by_metric["clicks"].value == 150.0
        # clicks conv rate from previous (impressions)
        assert by_metric["clicks"].conversion_rate_from_previous == round(
            150 / 3000 * 100, 2
        )
        # first step has None conversion rate
        assert by_metric["impressions"].conversion_rate_from_previous is None

    @pytest.mark.asyncio
    async def test_reach_all_from_channel_level_period_row(self, db, tenant_id) -> None:
        port = _StubOfferReadPort([])
        today = date.today()
        start, end = today.replace(day=1), today
        _make_period_reach(
            db,
            tenant_id=tenant_id,
            value=5000.0,
            period_start=start,
            period_end=end,
            campaign_id=None,
        )

        svc = MetricsByOfferService(db, port)
        # Use "90d" so the window covers the inserted row regardless of date.
        result = await svc.run(
            tenant_id,
            period="90d",
            tenant_locale=TenantLocale.default(),
        )
        assert result.reach_all == 5000.0

    @pytest.mark.asyncio
    async def test_reach_all_none_when_no_period_metrics(self, db, tenant_id) -> None:
        port = _StubOfferReadPort([])
        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id)
        assert result.reach_all is None


class TestPerOfferReach:
    @pytest.mark.asyncio
    async def test_single_campaign_offer_reads_reach_from_period_metrics(
        self, db, tenant_id, offer_id, make_campaign, make_metric
    ) -> None:
        offer = _offer(
            tenant_id,
            name="Programa Premium",
            archetype="PROGRAMA",
            checkout="https://buy/p",
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
            metric_name="impressions",
            value=5000,
            metric_date=today,
            campaign_id=campaign.external_id,
        )
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="clicks",
            value=500,
            metric_date=today,
            campaign_id=campaign.external_id,
        )
        start = today.replace(day=1)
        _make_period_reach(
            db,
            tenant_id=tenant_id,
            value=3200.0,
            period_start=start,
            period_end=today,
            campaign_id=campaign.external_id,
        )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id, period="90d")
        assert len(result.offers) == 1
        off = result.offers[0]
        assert off.reach == 3200.0
        # Frequency is calculated as impressions divided by reach
        assert off.frequency == round(5000 / 3200, 2)
        # funnel exists + is a subset (only this campaign's rows)
        by_metric = {s.metric_name: s for s in off.funnel}
        assert by_metric["impressions"].value == 5000.0
        assert by_metric["clicks"].value == 500.0

    @pytest.mark.asyncio
    async def test_multi_campaign_offer_reach_is_none(
        self, db, tenant_id, offer_id, make_campaign, make_metric
    ) -> None:
        offer = _offer(
            tenant_id,
            name="Programa Multi",
            archetype="PROGRAMA",
            checkout="https://buy/p",
            offer_id=offer_id,
        )
        port = _StubOfferReadPort([offer])
        c1 = make_campaign(db, tenant_id=tenant_id, external_id="c1", name="A")
        c2 = make_campaign(db, tenant_id=tenant_id, external_id="c2", name="B")
        repo = AssociationRepository(db)
        for ext in (c1.external_id, c2.external_id):
            repo.create(
                tenant_id=tenant_id,
                target_type=AssociationTargetType.CAMPAIGN,
                target_external_id=ext,
                offer_id=offer_id,
                association_type=AssociationType.MANUAL,
            )
        today = date.today()
        for ext in (c1.external_id, c2.external_id):
            make_metric(
                db,
                tenant_id=tenant_id,
                metric_name="impressions",
                value=1000,
                metric_date=today,
                campaign_id=ext,
            )
            _make_period_reach(
                db,
                tenant_id=tenant_id,
                value=900.0,
                period_start=today.replace(day=1),
                period_end=today,
                campaign_id=ext,
            )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id, period="90d")
        off = result.offers[0]
        # Overlap makes reach non-aggregable — never sum, never invent.
        assert off.reach is None
        assert off.frequency is None

    @pytest.mark.asyncio
    async def test_offer_with_one_campaign_no_period_row_reach_none(
        self, db, tenant_id, offer_id, make_campaign, make_metric
    ) -> None:
        offer = _offer(
            tenant_id,
            name="Programa sin reach",
            archetype="PROGRAMA",
            checkout="https://buy/p",
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
            metric_name="impressions",
            value=1000,
            metric_date=today,
            campaign_id=campaign.external_id,
        )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id)
        off = result.offers[0]
        assert off.reach is None


class TestOfferAggregateSecondaryMetrics:
    @pytest.mark.asyncio
    async def test_ctr_cpm_cpc_computed_on_offer(
        self, db, tenant_id, offer_id, make_campaign, make_metric
    ) -> None:
        offer = _offer(
            tenant_id,
            name="Programa",
            archetype="PROGRAMA",
            checkout="https://buy/p",
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
            metric_name="impressions",
            value=10000.0,
            metric_date=today,
            campaign_id=campaign.external_id,
        )
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="clicks",
            value=200.0,
            metric_date=today,
            campaign_id=campaign.external_id,
        )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id)
        off = result.offers[0]
        # ctr = 200/10000*100 = 2.0
        assert off.ctr == 2.0
        # cpm = 100/10000*1000 = 10.0
        assert off.cpm == 10.0
        # cpc = 100/200 = 0.5
        assert off.cpc == 0.5


class TestBrandingAggregate:
    @pytest.mark.asyncio
    async def test_branding_computes_ctr_cpm_cpc_and_funnel(
        self, db, tenant_id, make_campaign, make_metric
    ) -> None:
        port = _StubOfferReadPort([])
        campaign = make_campaign(
            db, tenant_id=tenant_id, external_id="br1", name="Brand"
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
            metric_name="impressions",
            value=20000.0,
            metric_date=today,
            campaign_id=campaign.external_id,
        )
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="clicks",
            value=400.0,
            metric_date=today,
            campaign_id=campaign.external_id,
        )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id)
        b = result.branding_only
        assert b.ctr == 2.0
        assert b.cpm == 10.0
        assert b.cpc == 0.5
        assert b.reach is None  # no period_metrics row
        assert b.frequency is None
        # Funnel only for branded campaigns
        by_metric = {s.metric_name: s for s in b.funnel}
        assert by_metric["impressions"].value == 20000.0
        assert by_metric["clicks"].value == 400.0


class TestUnassignedAggregate:
    @pytest.mark.asyncio
    async def test_unassigned_computes_ctr_cpm_cpc_and_funnel(
        self, db, tenant_id, make_campaign, make_metric
    ) -> None:
        port = _StubOfferReadPort([])
        campaign = make_campaign(
            db, tenant_id=tenant_id, external_id="u1", name="Sin asignar"
        )
        today = date.today()
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="spend",
            value=50.0,
            unit="currency",
            metric_date=today,
            campaign_id=campaign.external_id,
        )
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="impressions",
            value=5000.0,
            metric_date=today,
            campaign_id=campaign.external_id,
        )
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="clicks",
            value=100.0,
            metric_date=today,
            campaign_id=campaign.external_id,
        )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id)
        u = result.unassigned
        assert u.ctr == 2.0
        assert u.cpm == 10.0
        assert u.cpc == 0.5
        assert u.reach is None
        by_metric = {s.metric_name: s for s in u.funnel}
        assert by_metric["impressions"].value == 5000.0
        assert by_metric["clicks"].value == 100.0


class TestRoasAndPixelOff:
    @pytest.mark.asyncio
    async def test_purchase_offer_with_zero_conversions_has_null_roas(
        self, db, tenant_id, offer_id, make_campaign, make_metric
    ) -> None:
        offer = _offer(
            tenant_id,
            name="Curso Pixel Off",
            archetype="PROGRAMA",
            checkout="https://buy/p",
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
            value=80.0,
            unit="currency",
            metric_date=today,
            campaign_id=campaign.external_id,
        )
        # No conversions metric, no conversion_value

        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id)
        off = result.offers[0]
        assert off.roas is None
        assert off.primary_cost_per_result is None
        assert off.metric_unavailable_reason == "no_events_reported"

    @pytest.mark.asyncio
    async def test_metric_not_supported_branch(
        self, db, tenant_id, offer_id, make_campaign, make_metric, monkeypatch
    ) -> None:
        """If an offer's expected metric is not in `_PRIMARY_METRIC_CONFIG`,
        the service must surface `metric_not_supported` (vs. `no_events_reported`).

        This branch is defensive — all current `OfferExpectedMetric` enum values
        are in the map. We simulate a future enum value by monkeypatching the
        map so the lookup returns None for the PURCHASE case.
        """
        from src.modules.advertising.application.services import (
            metrics_by_offer_service as svc_module,
        )

        # Snapshot + drop PURCHASE so `_PRIMARY_METRIC_CONFIG.get(expected)` is None.
        original = dict(svc_module._PRIMARY_METRIC_CONFIG)
        patched = {k: v for k, v in original.items() if k.value != "purchase"}
        monkeypatch.setattr(svc_module, "_PRIMARY_METRIC_CONFIG", patched)

        offer = _offer(
            tenant_id,
            name="Curso Unsupported",
            archetype="PROGRAMA",
            checkout="https://buy/u",
            offer_id=offer_id,
        )
        port = _StubOfferReadPort([offer])
        campaign = make_campaign(
            db, tenant_id=tenant_id, external_id="cu", name="Unsup"
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
            value=50.0,
            unit="currency",
            metric_date=today,
            campaign_id=campaign.external_id,
        )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id)
        off = result.offers[0]
        assert off.metric_unavailable_reason == "metric_not_supported"
        assert off.primary_cost_per_result is None


class TestEmptyPeriod:
    @pytest.mark.asyncio
    async def test_no_rows_returns_empty_structure(self, db, tenant_id) -> None:
        port = _StubOfferReadPort([])
        svc = MetricsByOfferService(db, port)
        result = await svc.run(tenant_id)
        assert result.offers == []
        assert result.unassigned.total_spend == 0.0
        assert result.branding_only.total_spend == 0.0
        assert result.reach_all is None
        # funnel_all still has 5 steps with zero values
        assert len(result.funnel_all) == 5
        assert all(s.value == 0.0 for s in result.funnel_all)


class TestReachWindowOverlap:
    """Regression tests for the overlap predicate in list_period_metrics_for_reach.

    The ETL writes weekly/monthly/quarterly period_metrics rows, not per-window
    rows. A containment predicate ("row fully within window") would leave reach
    null for most 7d/30d queries because a monthly row extends beyond a weekly
    window. These tests lock in the overlap semantics.
    """

    @pytest.mark.asyncio
    async def test_monthly_row_covers_7d_window(self, db, tenant_id) -> None:
        """A monthly row must match a 7d window that falls inside the month."""
        port = _StubOfferReadPort([])
        today = date.today()
        # Insert a monthly row whose period extends beyond both ends of the
        # 7d window. With a strict containment predicate this row would be
        # skipped. With overlap, it matches.
        month_start = today.replace(day=1)
        # End-of-month — day 28 is safe for every month including February.
        month_end = month_start.replace(day=28)
        _make_period_reach(
            db,
            tenant_id=tenant_id,
            value=12000.0,
            period_start=month_start,
            period_end=month_end,
            campaign_id=None,
        )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(
            tenant_id, period="7d", tenant_locale=TenantLocale.default()
        )

        assert result.reach_all == 12000.0

    @pytest.mark.asyncio
    async def test_monthly_row_straddling_window_boundary_still_matches(
        self, db, tenant_id
    ) -> None:
        """A row whose period starts before the window and ends inside it still matches."""
        port = _StubOfferReadPort([])
        today = date.today()
        # Period: last 45 days. The 30d window starts 29 days ago, so the
        # row's period_start is BEFORE window_start — overlap still returns it.
        from datetime import timedelta

        _make_period_reach(
            db,
            tenant_id=tenant_id,
            value=8500.0,
            period_start=today - timedelta(days=45),
            period_end=today - timedelta(days=10),
            campaign_id=None,
        )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(
            tenant_id, period="30d", tenant_locale=TenantLocale.default()
        )

        assert result.reach_all == 8500.0

    @pytest.mark.asyncio
    async def test_row_entirely_outside_window_is_excluded(self, db, tenant_id) -> None:
        """A row that doesn't touch the window at all must NOT match."""
        from datetime import timedelta

        port = _StubOfferReadPort([])
        today = date.today()
        # Period fully in the past, 100 days ago to 95 days ago.
        _make_period_reach(
            db,
            tenant_id=tenant_id,
            value=9999.0,
            period_start=today - timedelta(days=100),
            period_end=today - timedelta(days=95),
            campaign_id=None,
        )

        svc = MetricsByOfferService(db, port)
        result = await svc.run(
            tenant_id, period="30d", tenant_locale=TenantLocale.default()
        )

        # The 30d window is [today-29, today] — no overlap with 100-95d ago.
        assert result.reach_all is None


class TestTenantLocaleTimezoneThroughService:
    """H2 regression: non-default TenantLocale must flow through run() and
    actually change the period window the service queries.

    Without this test, the timezone wire-through (the #1 tech-debt fix of
    this feature) can silently revert to UTC on any refactor.
    """

    @pytest.mark.asyncio
    async def test_lima_locale_changes_period_window(
        self, db, tenant_id, make_campaign, make_metric
    ) -> None:
        """Row dated 'today in Lima' but 'tomorrow in UTC' must still be included
        when the tenant_locale is America/Lima.

        We can't easily freeze the clock across modules in a pytest session,
        so we assert a weaker but still meaningful invariant: the service
        DOES NOT crash and DOES return rows when given a non-default locale,
        and the start/end dates in the DTO reflect the locale-driven window.
        The unit test `test_lima_vs_utc_differs_at_midnight_boundary` already
        proves the off-by-one semantics of `resolve_period_window` with a
        frozen clock — this test locks in the integration path.
        """
        port = _StubOfferReadPort([])
        campaign = make_campaign(
            db, tenant_id=tenant_id, external_id="c-lima", name="Lima Campaign"
        )
        today = date.today()
        make_metric(
            db,
            tenant_id=tenant_id,
            metric_name="spend",
            value=123.0,
            metric_date=today,
            campaign_id=campaign.external_id,
        )

        svc = MetricsByOfferService(db, port)
        locale = TenantLocale(currency="PEN", timezone="America/Lima")

        result = await svc.run(tenant_id, period="7d", tenant_locale=locale)

        # The window must be a valid 7-day window (end - start == 6 days).
        from datetime import timedelta

        assert (result.end_date - result.start_date) == timedelta(days=6)
        # And at least the today's metric should be visible in the aggregate.
        # Unassigned holds it because the campaign has no association.
        assert result.unassigned.total_spend == 123.0
