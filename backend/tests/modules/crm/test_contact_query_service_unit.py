"""Unit tests — ContactQueryService filter logic.

PR-2 PI-11: coverage lift para contact_query_service.py (69% → ≥90%).
Tests cubren combinaciones de filtros que los tests de API existentes
no alcanzan, usando mocks de session + CampaignsLookupPort para
mantener la suite rápida y desacoplada de Postgres.

Estrategia:
- _build_base_query y sub-helpers se verifican indirectamente via
  list_contacts (el servicio no tiene método público por sub-helper).
- El patrón es: mock AsyncSession que retorna resultados controlados,
  verificar que los filtros se apliquen correctamente (via assert sobre
  los resultados proyectados).
- Para las rutas de engagement (has_campaign_engagement=True/False)
  se mockea CampaignsLookupPort.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.modules.crm.api.dto.contact_filters import ContactFilterParams
from src.modules.crm.application.services.contact_query_service import (
    ContactQueryService,
)
from src.shared.domain.base_entity import Base
from src.shared.domain.enums import LifecycleStage
from src.shared.infrastructure.models.crm import (
    CustomerProfileModel,
    LeadModel,
)

TENANT_A = uuid4()
TENANT_B = uuid4()
NOW = datetime.now(tz=timezone.utc)

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Async DB fixtures (SQLite in-memory)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def async_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    yield engine


@pytest.fixture()
async def async_session(async_engine):
    """AsyncSession con schema completo + rollback per test."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


# ---------------------------------------------------------------------------
# Helpers de seed
# ---------------------------------------------------------------------------


def _make_profile(
    tenant_id: UUID,
    *,
    lifecycle_stage: LifecycleStage = LifecycleStage.LEAD,
    lead_score: float = 30.0,
    is_inactive: bool = False,
    primary_email: str | None = "contact@example.com",
    primary_phone: str | None = None,
    full_name: str | None = "Test Contact",
    lead_source: str | None = None,
    last_activity_at: datetime | None = None,
    created_at: datetime | None = None,
) -> CustomerProfileModel:
    return CustomerProfileModel(
        id=uuid4(),
        tenant_id=tenant_id,
        full_name=full_name,
        primary_email=primary_email,
        primary_phone=primary_phone,
        lifecycle_stage=lifecycle_stage,
        lead_score=lead_score,
        is_inactive=is_inactive,
        lead_source=lead_source,
        last_activity_at=last_activity_at or NOW,
        created_at=created_at or NOW,
        lifetime_value=0.0,
        traits={},
        computed_traits={},
    )


def _make_lead(
    tenant_id: UUID,
    customer_id: UUID,
    *,
    telegram_id: str | None = None,
    whatsapp_id: str | None = None,
    instagram_id: str | None = None,
    tiktok_id: str | None = None,
    country: str | None = None,
) -> LeadModel:
    return LeadModel(
        id=uuid4(),
        tenant_id=tenant_id,
        customer_id=customer_id,
        telegram_id=telegram_id,
        whatsapp_id=whatsapp_id,
        instagram_id=instagram_id,
        tiktok_id=tiktok_id,
        country=country,
        fit_score=0,
        intent_score=0,
        temperature="COLD",
        is_blacklisted=False,
        profile_data={},
    )


def _null_lookup() -> AsyncMock:
    """CampaignsLookupPort que retorna engagement vacío (no engagement)."""
    mock = AsyncMock()
    mock.find_recent_campaign_tasks_for_leads = AsyncMock(return_value={})
    return mock


def _svc(session: AsyncSession, lookup=None) -> ContactQueryService:
    return ContactQueryService(session=session, campaigns_lookup=lookup or _null_lookup())


# ---------------------------------------------------------------------------
# TestLifecycleScoreFilters
# ---------------------------------------------------------------------------


class TestLifecycleScoreFilters:
    """Cubre líneas #256-264 (lifecycle_stage_in, score_min, score_max, source_in)."""

    async def test_lifecycle_stage_in_filters_correctly(self, async_session):
        """Solo retorna profiles que coinciden con lifecycle_stage_in."""
        lead_p = _make_profile(TENANT_A, lifecycle_stage=LifecycleStage.LEAD)
        sub_p = _make_profile(TENANT_A, lifecycle_stage=LifecycleStage.SUBSCRIBER, primary_email="sub@x.com")
        async_session.add_all([lead_p, sub_p])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(lifecycle_stage_in=[LifecycleStage.LEAD])
        result = await svc.list_contacts(
            tenant_id=TENANT_A,
            filters=filters,
            limit=10,
            offset=0,
        )

        assert result.total_count == 1
        assert str(result.items[0].id) == str(lead_p.id)

    async def test_score_min_filter(self, async_session):
        """score_min excluye profiles con lead_score bajo."""
        high = _make_profile(TENANT_A, lead_score=80.0)
        low = _make_profile(TENANT_A, lead_score=10.0, primary_email="low@x.com")
        async_session.add_all([high, low])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(score_min=50)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].lead_score == 80.0

    async def test_score_max_filter(self, async_session):
        """score_max excluye profiles con lead_score alto."""
        high = _make_profile(TENANT_A, lead_score=90.0)
        low = _make_profile(TENANT_A, lead_score=20.0, primary_email="low@x.com")
        async_session.add_all([high, low])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(score_max=50)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].lead_score == 20.0

    async def test_source_in_filter(self, async_session):
        """source_in filtra por lead_source."""
        telegram_p = _make_profile(TENANT_A, lead_source="telegram")
        web_p = _make_profile(TENANT_A, lead_source="web", primary_email="web@x.com")
        async_session.add_all([telegram_p, web_p])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(source_in=["telegram"])
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].lead_source == "telegram"

    async def test_score_min_and_max_combined(self, async_session):
        """Combinar score_min + score_max filtra rango correcto."""
        mid = _make_profile(TENANT_A, lead_score=50.0)
        low = _make_profile(TENANT_A, lead_score=20.0, primary_email="low@x.com")
        high = _make_profile(TENANT_A, lead_score=90.0, primary_email="high@x.com")
        async_session.add_all([mid, low, high])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(score_min=40, score_max=60)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].lead_score == 50.0


# ---------------------------------------------------------------------------
# TestIdentityFilters
# ---------------------------------------------------------------------------


class TestIdentityFilters:
    """Cubre líneas #273-283 (has_email True/False, has_phone True/False)."""

    async def test_has_email_true_includes_profiles_with_email(self, async_session):
        with_email = _make_profile(TENANT_A, primary_email="yes@x.com")
        without_email = _make_profile(TENANT_A, primary_email=None, full_name="NoEmail")
        async_session.add_all([with_email, without_email])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(has_email=True)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].has_email is True

    async def test_has_email_false_includes_profiles_without_email(self, async_session):
        with_email = _make_profile(TENANT_A, primary_email="yes@x.com")
        without_email = _make_profile(TENANT_A, primary_email=None, full_name="NoEmail")
        async_session.add_all([with_email, without_email])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(has_email=False)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].has_email is False

    async def test_has_phone_true(self, async_session):
        with_phone = _make_profile(TENANT_A, primary_phone="+5491155555")
        no_phone = _make_profile(TENANT_A, primary_phone=None, primary_email="noph@x.com")
        async_session.add_all([with_phone, no_phone])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(has_phone=True)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].has_phone is True

    async def test_has_phone_false(self, async_session):
        with_phone = _make_profile(TENANT_A, primary_phone="+5491155555")
        no_phone = _make_profile(TENANT_A, primary_phone=None, primary_email="noph@x.com")
        async_session.add_all([with_phone, no_phone])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(has_phone=False)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].has_phone is False


# ---------------------------------------------------------------------------
# TestChannelPresenceFilters
# ---------------------------------------------------------------------------


class TestChannelPresenceFilters:
    """Cubre líneas #312-317 (_apply_channel_presence_filters vía Lead correlated EXISTS)."""

    async def test_has_telegram_id_true(self, async_session):
        p_tg = _make_profile(TENANT_A, primary_email="tg@x.com")
        p_no_tg = _make_profile(TENANT_A, primary_email="notg@x.com")
        async_session.add_all([p_tg, p_no_tg])
        await async_session.flush()

        lead_tg = _make_lead(TENANT_A, p_tg.id, telegram_id="tg-123")
        async_session.add(lead_tg)
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(has_telegram_id=True)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1

    async def test_has_telegram_id_false(self, async_session):
        p_tg = _make_profile(TENANT_A, primary_email="tg@x.com")
        p_no_tg = _make_profile(TENANT_A, primary_email="notg@x.com")
        async_session.add_all([p_tg, p_no_tg])
        await async_session.flush()

        lead_tg = _make_lead(TENANT_A, p_tg.id, telegram_id="tg-123")
        async_session.add(lead_tg)
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(has_telegram_id=False)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        # p_no_tg no tiene lead con telegram_id → included
        assert result.total_count == 1

    async def test_has_whatsapp_id_true(self, async_session):
        p_wa = _make_profile(TENANT_A, primary_email="wa@x.com")
        async_session.add(p_wa)
        await async_session.flush()

        lead_wa = _make_lead(TENANT_A, p_wa.id, whatsapp_id="wa-abc")
        async_session.add(lead_wa)
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(has_whatsapp_id=True)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1

    async def test_has_instagram_id_true(self, async_session):
        p_ig = _make_profile(TENANT_A, primary_email="ig@x.com")
        async_session.add(p_ig)
        await async_session.flush()

        lead_ig = _make_lead(TENANT_A, p_ig.id, instagram_id="ig-xyz")
        async_session.add(lead_ig)
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(has_instagram_id=True)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1

    async def test_has_tiktok_id_true(self, async_session):
        p_tt = _make_profile(TENANT_A, primary_email="tt@x.com")
        async_session.add(p_tt)
        await async_session.flush()

        lead_tt = _make_lead(TENANT_A, p_tt.id, tiktok_id="tt-def")
        async_session.add(lead_tt)
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(has_tiktok_id=True)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1


# ---------------------------------------------------------------------------
# TestTemporalFilters
# ---------------------------------------------------------------------------


class TestTemporalFilters:
    """Cubre líneas #325-334 (_apply_temporal_filters)."""

    async def test_created_after_filter(self, async_session):
        from datetime import timedelta

        old = _make_profile(TENANT_A, created_at=NOW - timedelta(days=10), primary_email="old@x.com")
        new = _make_profile(TENANT_A, created_at=NOW, primary_email="new@x.com")
        async_session.add_all([old, new])
        await async_session.flush()

        svc = _svc(async_session)
        cutoff = NOW - timedelta(days=5)
        filters = ContactFilterParams(created_after=cutoff)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].primary_email == "new@x.com"

    async def test_created_before_filter(self, async_session):
        from datetime import timedelta

        old = _make_profile(TENANT_A, created_at=NOW - timedelta(days=10), primary_email="old@x.com")
        new = _make_profile(TENANT_A, created_at=NOW, primary_email="new@x.com")
        async_session.add_all([old, new])
        await async_session.flush()

        svc = _svc(async_session)
        cutoff = NOW - timedelta(days=5)
        filters = ContactFilterParams(created_before=cutoff)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].primary_email == "old@x.com"

    async def test_last_activity_after_filter(self, async_session):
        from datetime import timedelta

        recent = _make_profile(TENANT_A, last_activity_at=NOW, primary_email="rec@x.com")
        stale = _make_profile(TENANT_A, last_activity_at=NOW - timedelta(days=30), primary_email="stale@x.com")
        async_session.add_all([recent, stale])
        await async_session.flush()

        svc = _svc(async_session)
        cutoff = NOW - timedelta(days=7)
        filters = ContactFilterParams(last_activity_after=cutoff)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].primary_email == "rec@x.com"

    async def test_last_activity_before_filter(self, async_session):
        from datetime import timedelta

        recent = _make_profile(TENANT_A, last_activity_at=NOW, primary_email="rec@x.com")
        stale = _make_profile(TENANT_A, last_activity_at=NOW - timedelta(days=30), primary_email="stale@x.com")
        async_session.add_all([recent, stale])
        await async_session.flush()

        svc = _svc(async_session)
        cutoff = NOW - timedelta(days=7)
        filters = ContactFilterParams(last_activity_before=cutoff)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].primary_email == "stale@x.com"

    async def test_is_inactive_true_filter(self, async_session):
        active = _make_profile(TENANT_A, is_inactive=False, primary_email="active@x.com")
        inactive = _make_profile(TENANT_A, is_inactive=True, primary_email="inactive@x.com")
        async_session.add_all([active, inactive])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(is_inactive=True)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].is_inactive is True

    async def test_is_inactive_false_filter(self, async_session):
        active = _make_profile(TENANT_A, is_inactive=False, primary_email="active@x.com")
        inactive = _make_profile(TENANT_A, is_inactive=True, primary_email="inactive@x.com")
        async_session.add_all([active, inactive])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(is_inactive=False)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].is_inactive is False


# ---------------------------------------------------------------------------
# TestGeoSearchFilters
# ---------------------------------------------------------------------------


class TestGeoSearchFilters:
    """Cubre líneas #344-364 (_apply_geo_search_filters: country_in + q)."""

    async def test_country_in_filter(self, async_session):
        p_mx = _make_profile(TENANT_A, primary_email="mx@x.com")
        p_pe = _make_profile(TENANT_A, primary_email="pe@x.com")
        async_session.add_all([p_mx, p_pe])
        await async_session.flush()

        lead_mx = _make_lead(TENANT_A, p_mx.id, country="mx")
        lead_pe = _make_lead(TENANT_A, p_pe.id, country="pe")
        async_session.add_all([lead_mx, lead_pe])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(country_in=["mx"])
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].country == "mx"

    async def test_q_search_by_name(self, async_session):
        john = _make_profile(TENANT_A, full_name="John Doe", primary_email="john@x.com")
        jane = _make_profile(TENANT_A, full_name="Jane Smith", primary_email="jane@x.com")
        async_session.add_all([john, jane])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(q="John")
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].full_name == "John Doe"

    async def test_q_search_by_email(self, async_session):
        p = _make_profile(TENANT_A, primary_email="unique_email@example.com", full_name="Email Search Test")
        other = _make_profile(TENANT_A, primary_email="other@x.com", full_name="Other Contact")
        async_session.add_all([p, other])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(q="unique_email")
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].primary_email == "unique_email@example.com"

    async def test_q_empty_string_returns_all(self, async_session):
        """q='   ' (solo whitespace) no filtra — devuelve todos."""
        p1 = _make_profile(TENANT_A, primary_email="a@x.com")
        p2 = _make_profile(TENANT_A, primary_email="b@x.com")
        async_session.add_all([p1, p2])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams(q="   ")
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 2


# ---------------------------------------------------------------------------
# TestEngagementFilter
# ---------------------------------------------------------------------------


class TestEngagementFilter:
    """Cubre líneas #99-111 (has_campaign_engagement True/False branch) y
    #386-418 (_resolve_engagement_filter), #388-389 (empty candidates).
    """

    async def test_engagement_true_includes_engaged_profiles(self, async_session):
        """has_campaign_engagement=True — solo retorna profiles con engagement."""
        p_engaged = _make_profile(TENANT_A, primary_email="engaged@x.com")
        p_not_engaged = _make_profile(TENANT_A, primary_email="not_engaged@x.com")
        async_session.add_all([p_engaged, p_not_engaged])
        await async_session.flush()

        lead_engaged = _make_lead(TENANT_A, p_engaged.id, whatsapp_id="wa-engaged")
        async_session.add(lead_engaged)
        await async_session.flush()

        # Mock: lookup retorna engagement solo para el lead_engaged
        mock_lookup = AsyncMock()
        mock_lookup.find_recent_campaign_tasks_for_leads = AsyncMock(return_value={lead_engaged.id: MagicMock()})

        svc = ContactQueryService(session=async_session, campaigns_lookup=mock_lookup)
        filters = ContactFilterParams(has_campaign_engagement=True)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].has_recent_campaign_engagement is True

    async def test_engagement_false_excludes_engaged_profiles(self, async_session):
        """has_campaign_engagement=False — excluye profiles con engagement."""
        p_engaged = _make_profile(TENANT_A, primary_email="engaged@x.com")
        p_not_engaged = _make_profile(TENANT_A, primary_email="not_engaged@x.com")
        async_session.add_all([p_engaged, p_not_engaged])
        await async_session.flush()

        lead_engaged = _make_lead(TENANT_A, p_engaged.id, whatsapp_id="wa-engaged")
        async_session.add(lead_engaged)
        await async_session.flush()

        mock_lookup = AsyncMock()
        mock_lookup.find_recent_campaign_tasks_for_leads = AsyncMock(return_value={lead_engaged.id: MagicMock()})

        svc = ContactQueryService(session=async_session, campaigns_lookup=mock_lookup)
        filters = ContactFilterParams(has_campaign_engagement=False)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].primary_email == "not_engaged@x.com"

    async def test_engagement_empty_candidates_returns_empty(self, async_session):
        """Si no hay candidatos, _resolve_engagement_filter retorna {} (líneas #388-389)."""
        # No profiles seeded → candidatos vacíos
        mock_lookup = AsyncMock()
        mock_lookup.find_recent_campaign_tasks_for_leads = AsyncMock(return_value={})

        svc = ContactQueryService(session=async_session, campaigns_lookup=mock_lookup)
        filters = ContactFilterParams(has_campaign_engagement=True)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 0

    async def test_engagement_no_leads_returns_empty_map(self, async_session):
        """Si candidatos no tienen leads, retorna {} sin llamar al port (línea #399-400)."""
        # Profile existe pero sin Lead asociado
        p = _make_profile(TENANT_A, primary_email="nolead@x.com")
        async_session.add(p)
        await async_session.flush()

        mock_lookup = AsyncMock()
        mock_lookup.find_recent_campaign_tasks_for_leads = AsyncMock(return_value={})

        svc = ContactQueryService(session=async_session, campaigns_lookup=mock_lookup)
        filters = ContactFilterParams(has_campaign_engagement=True)
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        # p no tiene leads → engagement vacío → no es engaged → 0 retornados con True
        assert result.total_count == 0


# ---------------------------------------------------------------------------
# TestPagination
# ---------------------------------------------------------------------------


class TestPagination:
    """Cubre lógica de paginación: offset, limit, has_more."""

    async def test_pagination_offset_and_limit(self, async_session):
        profiles = [_make_profile(TENANT_A, primary_email=f"p{i}@x.com", full_name=f"Contact {i}") for i in range(5)]
        async_session.add_all(profiles)
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams()
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=2, offset=0)

        assert result.total_count == 5
        assert len(result.items) == 2
        assert result.has_more is True

    async def test_pagination_last_page(self, async_session):
        profiles = [_make_profile(TENANT_A, primary_email=f"pp{i}@x.com", full_name=f"Contact {i}") for i in range(3)]
        async_session.add_all(profiles)
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams()
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=2)

        assert result.total_count == 3
        assert len(result.items) == 1
        assert result.has_more is False


# ---------------------------------------------------------------------------
# TestGetContactDetail
# ---------------------------------------------------------------------------


class TestGetContactDetail:
    """Cubre líneas #183-226 (get_contact_detail: found=True/False, con/sin lead, identidades)."""

    async def test_get_contact_detail_not_found(self, async_session):
        svc = _svc(async_session)
        result = await svc.get_contact_detail(tenant_id=TENANT_A, contact_id=uuid4())
        assert result is None

    async def test_get_contact_detail_wrong_tenant_returns_none(self, async_session):
        """Tenant isolation: profile de TENANT_B no visible desde TENANT_A."""
        p = _make_profile(TENANT_B, primary_email="b@x.com")
        async_session.add(p)
        await async_session.flush()

        svc = _svc(async_session)
        result = await svc.get_contact_detail(tenant_id=TENANT_A, contact_id=p.id)
        assert result is None

    async def test_get_contact_detail_found_without_lead(self, async_session):
        p = _make_profile(TENANT_A, primary_email="nolead@x.com")
        async_session.add(p)
        await async_session.flush()

        svc = _svc(async_session)
        result = await svc.get_contact_detail(tenant_id=TENANT_A, contact_id=p.id)

        assert result is not None
        assert result.lead_id is None
        assert result.telegram_id is None

    async def test_get_contact_detail_found_with_lead(self, async_session):
        p = _make_profile(TENANT_A, primary_email="withlead@x.com")
        async_session.add(p)
        await async_session.flush()

        lead = _make_lead(TENANT_A, p.id, telegram_id="tg-detail")
        async_session.add(lead)
        await async_session.flush()

        svc = _svc(async_session)
        result = await svc.get_contact_detail(tenant_id=TENANT_A, contact_id=p.id)

        assert result is not None
        assert result.lead_id is not None
        assert result.telegram_id == "tg-detail"


# ---------------------------------------------------------------------------
# TestTenantIsolation
# ---------------------------------------------------------------------------


class TestTenantIsolation:
    """Asegura que queries no returnan data cross-tenant."""

    async def test_list_contacts_isolates_tenants(self, async_session):
        p_a = _make_profile(TENANT_A, primary_email="a@x.com")
        p_b = _make_profile(TENANT_B, primary_email="b@x.com")
        async_session.add_all([p_a, p_b])
        await async_session.flush()

        svc = _svc(async_session)
        filters = ContactFilterParams()
        result = await svc.list_contacts(tenant_id=TENANT_A, filters=filters, limit=10, offset=0)

        assert result.total_count == 1
        assert result.items[0].primary_email == "a@x.com"
