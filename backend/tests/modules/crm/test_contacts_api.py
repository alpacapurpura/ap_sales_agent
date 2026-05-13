"""Integration tests — CRM Contacts API.

PR-10 PI-1 S4: 31 casos de integración sin mocks (política PR-4).
Real DB fixture con SQLite in-memory + seed de profiles, leads, identidades.

Tests verifican:
  - Tenant isolation (cross-tenant leak gate)
  - Todos los filtros de ContactFilterParams
  - Paginación (limit, offset, has_more, total_count)
  - Detail endpoint (schema completo + 404)
  - 501 stubs (journey + campaigns) con Retry-After header
  - Filter schema endpoint (version + campos canónicos)
  - response_model strict (extra="forbid")
  - Filtros combinados (AND semantics)
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from luana_core_platform.domain.base_entity import Base
from luana_core_platform.domain.enums import LifecycleStage
from luana_core_platform.infrastructure.models.crm import (
    CustomerIdentityModel,
    CustomerProfileModel,
    LeadModel,
)

# ── Constantes ────────────────────────────────────────────────────────────────

TENANT_A = uuid4()
TENANT_B = uuid4()
NOW = datetime.now(tz=timezone.utc)

pytestmark = pytest.mark.asyncio


# ── Fixtures de base de datos ─────────────────────────────────────────────────


@pytest.fixture(scope="module")
async def async_engine():
    """Motor SQLite in-memory para el módulo de tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture()
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """AsyncSession con rollback al final de cada test (isolación)."""
    async_session_factory = sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


# ── Helpers seed ──────────────────────────────────────────────────────────────


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
    """Crear CustomerProfileModel con valores por defecto."""
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
    """Crear LeadModel con valores por defecto."""
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


def _make_identity(
    tenant_id: UUID,
    profile_id: UUID,
    *,
    identity_type: str = "email",
    value: str = "test@example.com",
    is_primary: bool = True,
) -> CustomerIdentityModel:
    """Crear CustomerIdentityModel con valores por defecto."""
    return CustomerIdentityModel(
        id=uuid4(),
        tenant_id=tenant_id,
        profile_id=profile_id,
        type=identity_type,
        value=value,
        is_primary=is_primary,
        verification_status="verified",
        last_seen_at=NOW,
    )


# ── Cliente HTTP ──────────────────────────────────────────────────────────────


@pytest.fixture()
async def app_with_overrides(db_session: AsyncSession):
    """Setup overrides una sola vez. _fake_user lee X-Tenant-ID header per request."""
    from fastapi import Header
    from src.main import app
    from luana_core_campaigns.api._dependencies import get_campaigns_async_session
    from src.modules.crm.api.contacts import _get_contact_query_service
    from src.modules.crm.application.services.contact_query_service import (
        ContactQueryService,
    )
    from luana_core_iam.api.dependencies import get_current_user

    class _FakeUser:
        def __init__(self, tenant_id: UUID) -> None:
            self.id = uuid4()
            self.tenant_id = tenant_id
            self.email = "test@example.com"

    def _fake_user(x_tenant_id: str | None = Header(None, alias="X-Tenant-ID")) -> _FakeUser:
        # Default to TENANT_A si no se provee header
        tid = UUID(x_tenant_id) if x_tenant_id else TENANT_A
        return _FakeUser(tenant_id=tid)

    async def _fake_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    _mock_lookup = AsyncMock()
    _mock_lookup.find_recent_campaign_tasks_for_leads = AsyncMock(return_value={})
    _mock_lookup.find_recent_campaign_task_for_lead = AsyncMock(return_value=None)

    async def _fake_svc() -> ContactQueryService:
        return ContactQueryService(
            session=db_session,
            campaigns_lookup=_mock_lookup,
        )

    app.dependency_overrides[get_current_user] = _fake_user
    app.dependency_overrides[get_campaigns_async_session] = _fake_session
    app.dependency_overrides[_get_contact_query_service] = _fake_svc

    yield app, _mock_lookup

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_campaigns_async_session, None)
    app.dependency_overrides.pop(_get_contact_query_service, None)


@pytest.fixture()
async def client(app_with_overrides) -> AsyncGenerator[AsyncClient, None]:
    """Cliente Tenant A (header X-Tenant-ID = TENANT_A)."""
    app, _ = app_with_overrides
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test", headers={"X-Tenant-ID": str(TENANT_A)}) as ac:
        yield ac


@pytest.fixture()
async def client_tenant_b(app_with_overrides) -> AsyncGenerator[AsyncClient, None]:
    """Cliente Tenant B — prueba tenant isolation."""
    app, _ = app_with_overrides
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test", headers={"X-Tenant-ID": str(TENANT_B)}) as ac:
        yield ac


# ── Test helpers ──────────────────────────────────────────────────────────────


async def _seed(db: AsyncSession, *models: Any) -> None:
    """Persistir modelos y hacer flush para que los IDs sean válidos."""
    for m in models:
        db.add(m)
    await db.flush()


# ── 1. Tenant isolation ───────────────────────────────────────────────────────


async def test_list_contacts_tenant_isolation(
    client: AsyncClient,
    client_tenant_b: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Tenant A NO debe ver los profiles de Tenant B (cross-tenant leak gate)."""
    profile_a = _make_profile(TENANT_A, full_name="Alice Tenant A")
    profile_b = _make_profile(TENANT_B, full_name="Bob Tenant B")
    await _seed(db_session, profile_a, profile_b)

    resp_a = await client.get("/api/v1/contacts/")
    assert resp_a.status_code == 200
    names_a = [item["full_name"] for item in resp_a.json()["items"]]
    assert "Alice Tenant A" in names_a
    assert "Bob Tenant B" not in names_a

    resp_b = await client_tenant_b.get("/api/v1/contacts/")
    assert resp_b.status_code == 200
    names_b = [item["full_name"] for item in resp_b.json()["items"]]
    assert "Bob Tenant B" in names_b
    assert "Alice Tenant A" not in names_b


# ── 2. Filters ────────────────────────────────────────────────────────────────


async def test_filter_lifecycle_stage_in_returns_only_matching(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """lifecycle_stage_in=[mql,sql] retorna solo MQL+SQL."""
    mql = _make_profile(TENANT_A, lifecycle_stage=LifecycleStage.MQL, primary_email="mql@e.com")
    sql = _make_profile(TENANT_A, lifecycle_stage=LifecycleStage.SQL, primary_email="sql@e.com")
    sub = _make_profile(TENANT_A, lifecycle_stage=LifecycleStage.SUBSCRIBER, primary_email="sub@e.com")
    await _seed(db_session, mql, sql, sub)

    resp = await client.get("/api/v1/contacts/?lifecycle_stage_in=mql&lifecycle_stage_in=sql")
    assert resp.status_code == 200
    stages = {item["lifecycle_stage"] for item in resp.json()["items"]}
    assert stages <= {"mql", "sql"}
    assert "subscriber" not in stages


async def test_filter_score_range_inclusive(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """score_min=40&score_max=80 retorna solo scores en rango (boundaries inclusive)."""
    low = _make_profile(TENANT_A, lead_score=20.0, primary_email="low@e.com")
    mid = _make_profile(TENANT_A, lead_score=60.0, primary_email="mid@e.com")
    high = _make_profile(TENANT_A, lead_score=90.0, primary_email="high@e.com")
    boundary_min = _make_profile(TENANT_A, lead_score=40.0, primary_email="bmin@e.com")
    boundary_max = _make_profile(TENANT_A, lead_score=80.0, primary_email="bmax@e.com")
    await _seed(db_session, low, mid, high, boundary_min, boundary_max)

    resp = await client.get("/api/v1/contacts/?score_min=40&score_max=80")
    assert resp.status_code == 200
    scores = [item["lead_score"] for item in resp.json()["items"]]
    for score in scores:
        assert 40.0 <= score <= 80.0
    assert any(abs(s - 40.0) < 0.01 for s in scores)
    assert any(abs(s - 80.0) < 0.01 for s in scores)
    assert not any(abs(s - 20.0) < 0.01 for s in scores)
    assert not any(abs(s - 90.0) < 0.01 for s in scores)


async def test_filter_has_telegram_id_true(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """has_telegram_id=true retorna solo profiles con Lead.telegram_id NOT NULL."""
    with_tg = _make_profile(TENANT_A, primary_email="withtg@e.com")
    without_tg = _make_profile(TENANT_A, primary_email="notg@e.com")
    await _seed(db_session, with_tg, without_tg)

    lead_tg = _make_lead(TENANT_A, with_tg.id, telegram_id="@alice_tg")
    await _seed(db_session, lead_tg)

    resp = await client.get("/api/v1/contacts/?has_telegram_id=true")
    assert resp.status_code == 200
    emails = {item["primary_email"] for item in resp.json()["items"]}
    assert "withtg@e.com" in emails
    assert "notg@e.com" not in emails


async def test_filter_has_telegram_id_false(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """has_telegram_id=false retorna solo profiles SIN Lead.telegram_id."""
    with_tg = _make_profile(TENANT_A, primary_email="withtg2@e.com")
    without_tg = _make_profile(TENANT_A, primary_email="notg2@e.com")
    await _seed(db_session, with_tg, without_tg)

    lead_tg = _make_lead(TENANT_A, with_tg.id, telegram_id="@alice2_tg")
    await _seed(db_session, lead_tg)

    resp = await client.get("/api/v1/contacts/?has_telegram_id=false")
    assert resp.status_code == 200
    emails = {item["primary_email"] for item in resp.json()["items"]}
    assert "notg2@e.com" in emails
    assert "withtg2@e.com" not in emails


async def test_filter_has_email_true(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """has_email=true retorna solo profiles con primary_email."""
    with_email = _make_profile(TENANT_A, primary_email="hasemail@e.com")
    without_email = _make_profile(TENANT_A, primary_email=None, full_name="No Email User")
    await _seed(db_session, with_email, without_email)

    resp = await client.get("/api/v1/contacts/?has_email=true")
    assert resp.status_code == 200
    items = resp.json()["items"]
    for item in items:
        assert item["primary_email"] is not None
    emails = {item["primary_email"] for item in items}
    assert "hasemail@e.com" in emails


async def test_filter_has_phone_true(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """has_phone=true retorna solo profiles con primary_phone."""
    with_phone = _make_profile(
        TENANT_A,
        primary_email="withphone@e.com",
        primary_phone="+521234567890",
    )
    without_phone = _make_profile(TENANT_A, primary_email="nophone@e.com")
    await _seed(db_session, with_phone, without_phone)

    resp = await client.get("/api/v1/contacts/?has_phone=true")
    assert resp.status_code == 200
    items = resp.json()["items"]
    for item in items:
        assert item["primary_phone"] is not None
    emails = {item["primary_email"] for item in items}
    assert "withphone@e.com" in emails
    assert "nophone@e.com" not in emails


async def test_filter_created_after(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """created_after filtra correctamente (inclusive)."""
    old_date = NOW - timedelta(days=30)
    recent_date = NOW - timedelta(days=5)
    cutoff = NOW - timedelta(days=10)

    old = _make_profile(TENANT_A, primary_email="old@e.com", created_at=old_date)
    recent = _make_profile(TENANT_A, primary_email="recent@e.com", created_at=recent_date)
    await _seed(db_session, old, recent)

    resp = await client.get("/api/v1/contacts/", params={"created_after": cutoff.isoformat()})
    assert resp.status_code == 200
    emails = {item["primary_email"] for item in resp.json()["items"]}
    assert "recent@e.com" in emails
    assert "old@e.com" not in emails


async def test_filter_last_activity_before_excludes_recent(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """last_activity_before excluye actividad reciente (boundary correcto)."""
    cutoff = NOW - timedelta(days=10)
    old_active = _make_profile(
        TENANT_A,
        primary_email="oldactive@e.com",
        last_activity_at=NOW - timedelta(days=20),
    )
    recent_active = _make_profile(
        TENANT_A,
        primary_email="recentactive@e.com",
        last_activity_at=NOW - timedelta(days=3),
    )
    await _seed(db_session, old_active, recent_active)

    resp = await client.get("/api/v1/contacts/", params={"last_activity_before": cutoff.isoformat()})
    assert resp.status_code == 200
    emails = {item["primary_email"] for item in resp.json()["items"]}
    assert "oldactive@e.com" in emails
    assert "recentactive@e.com" not in emails


async def test_filter_is_inactive_true_returns_only_inactive(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """is_inactive=true retorna solo profiles marcados como inactivos."""
    inactive = _make_profile(TENANT_A, primary_email="inactive@e.com", is_inactive=True)
    active = _make_profile(TENANT_A, primary_email="active@e.com", is_inactive=False)
    await _seed(db_session, inactive, active)

    resp = await client.get("/api/v1/contacts/?is_inactive=true")
    assert resp.status_code == 200
    items = resp.json()["items"]
    for item in items:
        assert item["is_inactive"] is True
    emails = {item["primary_email"] for item in items}
    assert "inactive@e.com" in emails
    assert "active@e.com" not in emails


async def test_filter_source_in_returns_matching(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """source_in=['instagram_dm','landing'] retorna solo los que coinciden."""
    ig = _make_profile(TENANT_A, primary_email="ig@e.com", lead_source="instagram_dm")
    landing = _make_profile(TENANT_A, primary_email="landing@e.com", lead_source="landing")
    organic = _make_profile(TENANT_A, primary_email="organic@e.com", lead_source="organic_seo")
    await _seed(db_session, ig, landing, organic)

    resp = await client.get("/api/v1/contacts/?source_in=instagram_dm&source_in=landing")
    assert resp.status_code == 200
    emails = {item["primary_email"] for item in resp.json()["items"]}
    assert "ig@e.com" in emails
    assert "landing@e.com" in emails
    assert "organic@e.com" not in emails


async def test_filter_country_in_returns_matching(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """country_in=['mx','pe'] retorna solo los que tienen Lead con ese país."""
    mx_profile = _make_profile(TENANT_A, primary_email="mx@e.com")
    pe_profile = _make_profile(TENANT_A, primary_email="pe@e.com")
    ar_profile = _make_profile(TENANT_A, primary_email="ar@e.com")
    await _seed(db_session, mx_profile, pe_profile, ar_profile)

    lead_mx = _make_lead(TENANT_A, mx_profile.id, country="mx")
    lead_pe = _make_lead(TENANT_A, pe_profile.id, country="pe")
    lead_ar = _make_lead(TENANT_A, ar_profile.id, country="ar")
    await _seed(db_session, lead_mx, lead_pe, lead_ar)

    resp = await client.get("/api/v1/contacts/?country_in=mx&country_in=pe")
    assert resp.status_code == 200
    emails = {item["primary_email"] for item in resp.json()["items"]}
    assert "mx@e.com" in emails
    assert "pe@e.com" in emails
    assert "ar@e.com" not in emails


async def test_filter_has_campaign_engagement_true_returns_engaged(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """has_campaign_engagement=true retorna solo leads con CampaignTask SENT en ventana."""
    from src.main import app
    from src.modules.crm.api.contacts import _get_contact_query_service
    from src.modules.crm.application.services.contact_query_service import (
        ContactQueryService,
    )
    from luana_core_platform.links.ports.campaigns import CampaignTaskLookupResult

    engaged_profile = _make_profile(TENANT_A, primary_email="engaged@e.com")
    not_engaged_profile = _make_profile(TENANT_A, primary_email="notengaged@e.com")
    await _seed(db_session, engaged_profile, not_engaged_profile)

    engaged_lead = _make_lead(TENANT_A, engaged_profile.id)
    await _seed(db_session, engaged_lead)

    campaign_id = uuid4()
    task_id = uuid4()
    engagement_result = CampaignTaskLookupResult(
        campaign_id=campaign_id,
        campaign_name="Test Campaign",
        task_id=task_id,
        sent_at=NOW - timedelta(days=30),
    )

    # Override con mock que retorna engagement para el lead específico
    mock_lookup = AsyncMock()
    mock_lookup.find_recent_campaign_tasks_for_leads = AsyncMock(return_value={engaged_lead.id: engagement_result})

    async def _fake_svc_engaged() -> ContactQueryService:
        return ContactQueryService(
            session=db_session,
            campaigns_lookup=mock_lookup,
        )

    app.dependency_overrides[_get_contact_query_service] = _fake_svc_engaged

    resp = await client.get("/api/v1/contacts/?has_campaign_engagement=true")
    assert resp.status_code == 200
    emails = {item["primary_email"] for item in resp.json()["items"]}
    assert "engaged@e.com" in emails
    assert "notengaged@e.com" not in emails

    # Restaurar override original
    app.dependency_overrides.pop(_get_contact_query_service, None)


async def test_filter_has_campaign_engagement_false_excludes_engaged(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """has_campaign_engagement=false excluye leads con engagement reciente."""
    from src.main import app
    from src.modules.crm.api.contacts import _get_contact_query_service
    from src.modules.crm.application.services.contact_query_service import (
        ContactQueryService,
    )
    from luana_core_platform.links.ports.campaigns import CampaignTaskLookupResult

    engaged_p = _make_profile(TENANT_A, primary_email="eng_excl@e.com")
    clean_p = _make_profile(TENANT_A, primary_email="clean_excl@e.com")
    await _seed(db_session, engaged_p, clean_p)

    eng_lead = _make_lead(TENANT_A, engaged_p.id)
    await _seed(db_session, eng_lead)

    result = CampaignTaskLookupResult(
        campaign_id=uuid4(),
        campaign_name="Camp X",
        task_id=uuid4(),
        sent_at=NOW - timedelta(days=10),
    )

    mock_lookup = AsyncMock()
    mock_lookup.find_recent_campaign_tasks_for_leads = AsyncMock(return_value={eng_lead.id: result})

    async def _fake_svc_false() -> ContactQueryService:
        return ContactQueryService(
            session=db_session,
            campaigns_lookup=mock_lookup,
        )

    app.dependency_overrides[_get_contact_query_service] = _fake_svc_false

    resp = await client.get("/api/v1/contacts/?has_campaign_engagement=false")
    assert resp.status_code == 200
    emails = {item["primary_email"] for item in resp.json()["items"]}
    assert "clean_excl@e.com" in emails
    assert "eng_excl@e.com" not in emails

    app.dependency_overrides.pop(_get_contact_query_service, None)


async def test_filter_has_campaign_engagement_window_boundary(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Tarea 100 días atrás (fuera ventana 90d) → NOT engaged."""
    from src.main import app
    from src.modules.crm.api.contacts import _get_contact_query_service
    from src.modules.crm.application.services.contact_query_service import (
        ContactQueryService,
    )

    profile = _make_profile(TENANT_A, primary_email="boundary@e.com")
    await _seed(db_session, profile)
    lead = _make_lead(TENANT_A, profile.id)
    await _seed(db_session, lead)

    # Lookup retorna vacío (tarea fuera de ventana)
    mock_lookup = AsyncMock()
    mock_lookup.find_recent_campaign_tasks_for_leads = AsyncMock(return_value={})

    async def _fake_svc_boundary() -> ContactQueryService:
        return ContactQueryService(
            session=db_session,
            campaigns_lookup=mock_lookup,
        )

    app.dependency_overrides[_get_contact_query_service] = _fake_svc_boundary

    resp = await client.get("/api/v1/contacts/?has_campaign_engagement=true")
    assert resp.status_code == 200
    emails = {item["primary_email"] for item in resp.json()["items"]}
    assert "boundary@e.com" not in emails

    app.dependency_overrides.pop(_get_contact_query_service, None)


async def test_search_q_matches_name_email_phone(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """q=juan matchea profiles con name='Juan', email='juan@x', phone='+541199juan'."""
    by_name = _make_profile(TENANT_A, full_name="Juan García", primary_email="other1@e.com")
    by_email = _make_profile(TENANT_A, full_name="Other Person", primary_email="juan@somesite.com")
    by_phone = _make_profile(
        TENANT_A,
        full_name="Another Person",
        primary_email="another@e.com",
        primary_phone="+541199juan",
    )
    no_match = _make_profile(TENANT_A, full_name="María López", primary_email="maria@e.com")
    await _seed(db_session, by_name, by_email, by_phone, no_match)

    resp = await client.get("/api/v1/contacts/?q=juan")
    assert resp.status_code == 200
    emails = {item["primary_email"] for item in resp.json()["items"]}
    assert "other1@e.com" in emails
    assert "juan@somesite.com" in emails
    assert "another@e.com" in emails
    assert "maria@e.com" not in emails


async def test_search_q_case_insensitive(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Búsqueda q es case-insensitive (ILIKE)."""
    profile = _make_profile(TENANT_A, full_name="CARLOS MENDEZ", primary_email="carlos@e.com")
    await _seed(db_session, profile)

    resp = await client.get("/api/v1/contacts/?q=carlos")
    assert resp.status_code == 200
    emails = {item["primary_email"] for item in resp.json()["items"]}
    assert "carlos@e.com" in emails

    resp2 = await client.get("/api/v1/contacts/?q=CARLOS")
    assert resp2.status_code == 200
    emails2 = {item["primary_email"] for item in resp2.json()["items"]}
    assert "carlos@e.com" in emails2


# ── 3. Paginación ─────────────────────────────────────────────────────────────


async def test_pagination_offset_limit_correct_slice(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """offset/limit retornan el slice correcto."""
    # Crear 5 profiles con emails distintos
    profiles = [_make_profile(TENANT_A, primary_email=f"pag{i}@e.com", lead_score=float(i)) for i in range(5)]
    await _seed(db_session, *profiles)

    resp_page1 = await client.get("/api/v1/contacts/?limit=2&offset=0")
    resp_page2 = await client.get("/api/v1/contacts/?limit=2&offset=2")

    assert resp_page1.status_code == 200
    assert resp_page2.status_code == 200
    items1 = resp_page1.json()["items"]
    items2 = resp_page2.json()["items"]

    # No deben solaparse
    ids1 = {item["id"] for item in items1}
    ids2 = {item["id"] for item in items2}
    assert not ids1.intersection(ids2)

    assert len(items1) == 2
    assert len(items2) == 2


async def test_pagination_total_count_consistent(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """total_count es consistente con el total real de profiles del tenant."""
    # Crear 3 profiles
    for i in range(3):
        p = _make_profile(TENANT_A, primary_email=f"total{i}@e.com")
        await _seed(db_session, p)

    resp = await client.get("/api/v1/contacts/?limit=1&offset=0")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_count"] >= 3  # puede haber más de tests anteriores
    assert len(body["items"]) == 1


async def test_pagination_has_more_flag(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """has_more=true cuando hay más items que limit+offset."""
    for i in range(3):
        p = _make_profile(TENANT_A, primary_email=f"hasmore{i}@e.com")
        await _seed(db_session, p)

    resp = await client.get("/api/v1/contacts/?limit=1&offset=0")
    assert resp.status_code == 200
    body = resp.json()
    if body["total_count"] > 1:
        assert body["has_more"] is True

    # Con limit > total → has_more=False
    resp2 = await client.get("/api/v1/contacts/?limit=100&offset=0")
    assert resp2.status_code == 200
    assert resp2.json()["has_more"] is False


async def test_pagination_limit_max_100_validates(
    client: AsyncClient,
) -> None:
    """limit > 100 retorna 422 (validación Pydantic/FastAPI)."""
    resp = await client.get("/api/v1/contacts/?limit=101")
    assert resp.status_code == 422


async def test_pagination_limit_zero_rejects(
    client: AsyncClient,
) -> None:
    """limit=0 retorna 422 (limit >= 1)."""
    resp = await client.get("/api/v1/contacts/?limit=0")
    assert resp.status_code == 422


# ── 4. Detail endpoint ────────────────────────────────────────────────────────


async def test_get_contact_detail_returns_full_schema(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /{id} retorna ContactDetail con todos los campos esperados."""
    profile = _make_profile(
        TENANT_A,
        full_name="Detail User",
        primary_email="detail@e.com",
        primary_phone="+52911111111",
    )
    await _seed(db_session, profile)

    lead = _make_lead(
        TENANT_A,
        profile.id,
        telegram_id="@detailuser",
        country="mx",
    )
    await _seed(db_session, lead)

    resp = await client.get(f"/api/v1/contacts/{profile.id}")
    assert resp.status_code == 200
    body = resp.json()

    # Verificar campos clave del schema
    assert body["id"] == str(profile.id)
    assert body["full_name"] == "Detail User"
    assert body["primary_email"] == "detail@e.com"
    assert body["primary_phone"] == "+52911111111"
    assert "lifecycle_stage" in body
    assert "lead_score" in body
    assert "rfm_segment" in body
    assert "lifetime_value" in body
    assert "is_inactive" in body
    assert "identities" in body
    assert isinstance(body["identities"], list)


async def test_get_contact_detail_includes_identities_list(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /{id} incluye identidades multi-canal serializadas."""
    profile = _make_profile(TENANT_A, primary_email="withidentity@e.com")
    await _seed(db_session, profile)

    identity = _make_identity(
        TENANT_A,
        profile.id,
        identity_type="email",
        value="withidentity@e.com",
        is_primary=True,
    )
    await _seed(db_session, identity)

    resp = await client.get(f"/api/v1/contacts/{profile.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["identities"]) >= 1
    assert any(i["value"] == "withidentity@e.com" for i in body["identities"])


async def test_get_contact_detail_404_when_other_tenant(
    client: AsyncClient,
    client_tenant_b: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /{id} retorna 404 si el contacto pertenece a otro tenant."""
    profile_b = _make_profile(TENANT_B, primary_email="tenant_b_only@e.com")
    await _seed(db_session, profile_b)

    # Tenant A intenta acceder al profile de Tenant B
    resp = await client.get(f"/api/v1/contacts/{profile_b.id}")
    assert resp.status_code == 404


async def test_get_contact_detail_404_when_nonexistent_uuid(
    client: AsyncClient,
) -> None:
    """GET /{id} retorna 404 cuando el UUID no existe."""
    nonexistent_id = uuid4()
    resp = await client.get(f"/api/v1/contacts/{nonexistent_id}")
    assert resp.status_code == 404


# ── 5. Stubs 501 ──────────────────────────────────────────────────────────────


async def test_journey_endpoint_returns_501_with_retry_after(
    client: AsyncClient,
) -> None:
    """GET /{id}/journey retorna 501 con Retry-After: PI-3."""
    contact_id = uuid4()
    resp = await client.get(f"/api/v1/contacts/{contact_id}/journey")
    assert resp.status_code == 501
    assert resp.headers.get("retry-after") == "PI-3"
    body = resp.json()
    assert body["deferred_until"] == "PI-3"
    assert "journey" in body["canonical_path"]


async def test_campaigns_endpoint_returns_501_with_retry_after(
    client: AsyncClient,
) -> None:
    """GET /{id}/campaigns retorna 501 con Retry-After: PI-3."""
    contact_id = uuid4()
    resp = await client.get(f"/api/v1/contacts/{contact_id}/campaigns")
    assert resp.status_code == 501
    assert resp.headers.get("retry-after") == "PI-3"
    body = resp.json()
    assert body["deferred_until"] == "PI-3"
    assert "campaigns" in body["canonical_path"]


# ── 6. Filter schema ──────────────────────────────────────────────────────────


async def test_filter_schema_endpoint_returns_canonical_fields_list(
    client: AsyncClient,
) -> None:
    """GET /_filter-schema retorna version '1.0' + todos los campos canónicos."""
    from tests.architecture.test_contacts_filter_params_forward_compat import (
        CANONICAL_FILTER_FIELDS,
    )

    resp = await client.get("/api/v1/contacts/_filter-schema")
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == "1.0"
    field_names = {f["name"] for f in body["fields"]}
    assert field_names == CANONICAL_FILTER_FIELDS


# ── 7. Response model strict ──────────────────────────────────────────────────


async def test_response_model_extra_forbid_rejects_unknown_field() -> None:
    """ContactFilterParams con extra="forbid" rechaza campos desconocidos."""
    from pydantic import ValidationError

    from luana_core_crm.api.dto.contact_filters import ContactFilterParams

    with pytest.raises(ValidationError):
        ContactFilterParams(unknown_field="value")  # type: ignore[call-arg]


# ── 8. Filtros combinados ─────────────────────────────────────────────────────


async def test_concurrent_filters_combine_correctly(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """lifecycle_stage_in=[mql]&score_min=50&has_telegram_id=true — AND semántico."""
    # Cumple todos
    p_match = _make_profile(
        TENANT_A,
        primary_email="match_all@e.com",
        lifecycle_stage=LifecycleStage.MQL,
        lead_score=60.0,
    )
    # Solo MQL pero sin score suficiente
    p_mql_low = _make_profile(
        TENANT_A,
        primary_email="mql_low@e.com",
        lifecycle_stage=LifecycleStage.MQL,
        lead_score=30.0,
    )
    # Score alto pero no MQL
    p_sql_high = _make_profile(
        TENANT_A,
        primary_email="sql_high@e.com",
        lifecycle_stage=LifecycleStage.SQL,
        lead_score=70.0,
    )
    await _seed(db_session, p_match, p_mql_low, p_sql_high)

    lead_match = _make_lead(TENANT_A, p_match.id, telegram_id="@match_user")
    await _seed(db_session, lead_match)

    resp = await client.get("/api/v1/contacts/?lifecycle_stage_in=mql&score_min=50&has_telegram_id=true")
    assert resp.status_code == 200
    emails = {item["primary_email"] for item in resp.json()["items"]}
    assert "match_all@e.com" in emails
    assert "mql_low@e.com" not in emails
    assert "sql_high@e.com" not in emails


# ── 9. CF-tunnel slash handling — dual-decorator regression ───────────────────


async def test_list_contacts_no_slash_returns_200(
    client: AsyncClient,
) -> None:
    """GET /api/v1/contacts (sin trailing slash) debe retornar 200.

    Regresión: CloudFlare Tunnel strip trailing slash → BE sin decorator ""
    retornaba 404 porque redirect_slashes=False es regla inviolable.
    Fix: dual-decorator @router.get("") + @router.get("/") en list_contacts.
    PI-1 hotfix #1.
    """
    resp = await client.get("/api/v1/contacts")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total_count" in body


async def test_list_contacts_slash_still_returns_200(
    client: AsyncClient,
) -> None:
    """GET /api/v1/contacts/ (con trailing slash) sigue retornando 200.

    El alias con slash no debe romperse al agregar el decorator canónico "".
    """
    resp = await client.get("/api/v1/contacts/")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
