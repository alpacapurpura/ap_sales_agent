"""Integration tests — SegmentCreate STATIC with lead_ids (PR-12 PI-1 S4).

Policy: sin mocks para servicios de negocio (política PR-4).
SQLite in-memory + seed de leads real. Servicios reales instanciados manualmente.

Casos cubiertos:
  1. STATIC snapshot persists lead_ids in JSONB with {"_static": true, "lead_ids": [...]}
  2. Validación ownership: lead_id de otro tenant → SegmentLeadOwnershipError
  3. Rechaza lead_ids vacío con STATIC → ValidationError (422)
  4. Rechaza filter_dsl + lead_ids juntos → ValidationError (422)
  5. DYNAMIC baseline preservado — no regresión
  6. resolve() STATIC devuelve persisted lead_ids sin SQL evaluation
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from luana_core_campaigns.application.dtos.segment_dtos import SegmentCreate, SegmentResponse
from luana_core_campaigns.application.services.segment_service import (
    SegmentLeadOwnershipError,
    SegmentService,
)
from luana_core_campaigns.domain.enums import SegmentType
from luana_core_campaigns.domain.segment_filter import PredefinedSegmentFilter
from luana_core_campaigns.infrastructure.models.segment_model import SegmentModel
from luana_core_campaigns.infrastructure.repositories.segment_repository_impl import (
    SegmentRepositoryImpl,
)
from luana_core_campaigns.infrastructure.repositories.segment_snapshot_repository_impl import (
    SegmentSnapshotRepositoryImpl,
)
from luana_core_platform.domain.base_entity import Base
from luana_core_platform.infrastructure.models.crm import LeadModel

# ── Constantes ─────────────────────────────────────────────────────────────────

TENANT_A = uuid4()
TENANT_B = uuid4()
NOW = datetime.now(tz=timezone.utc)

pytestmark = pytest.mark.asyncio


# ── Engine + session ───────────────────────────────────────────────────────────


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


# ── Helpers seed ───────────────────────────────────────────────────────────────


def _make_lead(tenant_id: UUID) -> LeadModel:
    """Crear LeadModel mínimo para seed."""
    return LeadModel(
        id=uuid4(),
        tenant_id=tenant_id,
        fit_score=0,
        intent_score=0,
        temperature="COLD",
        is_blacklisted=False,
        profile_data={},
    )


# ── Service factory (no inyección DI real — instancia directa) ────────────────


def _build_service() -> SegmentService:
    """Build SegmentService with minimal real repos + mock collaborators.

    LeadQueryPort mock: only used by DYNAMIC resolve(). For STATIC tests,
    resolve() short-circuits before calling LeadQueryPort.
    Cache mock: in-memory dict sufficient for test isolation.
    """
    repo = SegmentRepositoryImpl()
    snapshot_repo = SegmentSnapshotRepositoryImpl()

    # Outbox: best-effort write, mock to avoid outbox table in SQLite
    outbox_svc = AsyncMock()
    outbox_svc.enqueue_async_from_sync_caller = AsyncMock(return_value=None)

    # Cache: simple in-memory mock
    _cache_store: dict = {}

    async def _cache_get(key: str) -> object:
        return _cache_store.get(key)

    async def _cache_set(key: str, val: object, ttl: int | None = None) -> None:
        _cache_store[key] = val

    cache = MagicMock()
    cache.get = _cache_get
    cache.set = _cache_set
    cache.invalidate = AsyncMock(return_value=None)
    cache.invalidate_pattern = AsyncMock(return_value=None)

    # LeadQueryPort: used only by DYNAMIC path
    lead_query_port = AsyncMock()
    lead_query_port.list_lead_ids_matching = AsyncMock(return_value=([], 0))
    lead_query_port.count_leads_matching = AsyncMock(return_value=0)

    # SegmentFilterEvaluator: mock — only used by DYNAMIC resolve()
    filter_evaluator = MagicMock()
    from sqlalchemy import true as sqla_true

    filter_evaluator.to_sql_predicate = MagicMock(return_value=sqla_true())

    return SegmentService(
        repo=repo,
        snapshot_repo=snapshot_repo,
        lead_query_port=lead_query_port,
        filter_evaluator=filter_evaluator,
        outbox_service=outbox_svc,
        cache=cache,
    )


# ── Tests — STATIC creation ───────────────────────────────────────────────────


async def test_segment_create_static_with_lead_ids_persists_snapshot(db_session: AsyncSession) -> None:
    """STATIC create persists filter_dsl JSONB with _static:true + lead_ids snapshot."""
    # Seed 3 leads para TENANT_A
    lead_a = _make_lead(TENANT_A)
    lead_b = _make_lead(TENANT_A)
    lead_c = _make_lead(TENANT_A)
    db_session.add_all([lead_a, lead_b, lead_c])
    await db_session.flush()

    svc = _build_service()
    dto = SegmentCreate(
        name="Segmento prueba STATIC",
        description="Test PR-12",
        segment_type=SegmentType.STATIC,
        lead_ids=[lead_a.id, lead_b.id, lead_c.id],
    )
    segment = await svc.create(tenant_id=TENANT_A, dto=dto, session=db_session)

    # Verify domain entity
    assert segment.segment_type == SegmentType.STATIC
    assert segment.static_lead_ids is not None
    assert set(segment.static_lead_ids) == {lead_a.id, lead_b.id, lead_c.id}
    assert segment.estimated_size == 3

    # Verify JSONB persisted shape
    stmt = select(SegmentModel).where(SegmentModel.id == segment.id)
    result = await db_session.execute(stmt)
    row = result.scalar_one_or_none()
    assert row is not None
    assert row.filter_dsl["_static"] is True
    assert len(row.filter_dsl["lead_ids"]) == 3
    assert str(lead_a.id) in row.filter_dsl["lead_ids"]

    # Verify SegmentResponse serializes correctly
    response = SegmentResponse.model_validate(segment)
    assert response.segment_type == SegmentType.STATIC
    assert response.static_lead_ids is not None
    assert len(response.static_lead_ids) == 3
    assert response.filter_dsl is None or isinstance(response.filter_dsl, PredefinedSegmentFilter)


async def test_segment_create_static_validates_lead_ids_belong_to_tenant(
    db_session: AsyncSession,
) -> None:
    """STATIC create rejects lead_ids from a different tenant → SegmentLeadOwnershipError."""
    # Seed 1 lead para TENANT_B (alien lead)
    alien_lead = _make_lead(TENANT_B)
    own_lead = _make_lead(TENANT_A)
    db_session.add_all([alien_lead, own_lead])
    await db_session.flush()

    svc = _build_service()
    dto = SegmentCreate(
        name="Segmento alien",
        segment_type=SegmentType.STATIC,
        lead_ids=[own_lead.id, alien_lead.id],  # alien_lead.id belongs to TENANT_B
    )

    with pytest.raises(SegmentLeadOwnershipError):
        await svc.create(tenant_id=TENANT_A, dto=dto, session=db_session)


async def test_segment_create_static_rejects_empty_lead_ids() -> None:
    """STATIC segment with empty lead_ids list → Pydantic ValidationError (422)."""
    with pytest.raises(ValidationError) as exc_info:
        SegmentCreate(
            name="Segmento vacio",
            segment_type=SegmentType.STATIC,
            lead_ids=[],  # vacío — rechazado por model_validator
        )
    # Verify the error message mentions STATIC
    errors = exc_info.value.errors()
    assert any("STATIC" in str(e.get("msg", "")) or "lead_ids" in str(e.get("msg", "")) for e in errors)


async def test_segment_create_static_rejects_with_filter_dsl() -> None:
    """STATIC + filter_dsl simultaneously → Pydantic ValidationError (422)."""
    with pytest.raises(ValidationError):
        SegmentCreate(
            name="Segmento mixto",
            segment_type=SegmentType.STATIC,
            lead_ids=[uuid4()],
            filter_dsl=PredefinedSegmentFilter(),  # no debe estar presente en STATIC
        )


async def test_segment_create_dynamic_rejects_lead_ids() -> None:
    """DYNAMIC + lead_ids → Pydantic ValidationError (422). Baseline DYNAMIC invariant."""
    with pytest.raises(ValidationError):
        SegmentCreate(
            name="Segmento dinamico con lead_ids",
            segment_type=SegmentType.DYNAMIC,
            filter_dsl=PredefinedSegmentFilter(),
            lead_ids=[uuid4()],  # DYNAMIC no debe tener lead_ids
        )


async def test_segment_create_dynamic_still_works(db_session: AsyncSession) -> None:
    """DYNAMIC baseline preservado: create con filter_dsl funciona sin cambios."""
    svc = _build_service()
    dto = SegmentCreate(
        name="Segmento dinamico baseline",
        segment_type=SegmentType.DYNAMIC,
        filter_dsl=PredefinedSegmentFilter(lifecycle_stage=["SUBSCRIBER"]),
    )
    segment = await svc.create(tenant_id=TENANT_A, dto=dto, session=db_session)

    assert segment.segment_type == SegmentType.DYNAMIC
    assert segment.static_lead_ids is None
    assert segment.filter_dsl is not None
    assert segment.filter_dsl.lifecycle_stage == ["SUBSCRIBER"]

    # Verify JSONB shape is the standard filter (no _static key)
    stmt = select(SegmentModel).where(SegmentModel.id == segment.id)
    result = await db_session.execute(stmt)
    row = result.scalar_one_or_none()
    assert row is not None
    assert "_static" not in row.filter_dsl


async def test_segment_resolve_static_returns_persisted_lead_ids(db_session: AsyncSession) -> None:
    """resolve() STATIC devuelve lead_ids del snapshot sin SQL evaluation."""
    # Seed 2 leads
    lead_1 = _make_lead(TENANT_A)
    lead_2 = _make_lead(TENANT_A)
    db_session.add_all([lead_1, lead_2])
    await db_session.flush()

    svc = _build_service()
    dto = SegmentCreate(
        name="Segmento resolve test",
        segment_type=SegmentType.STATIC,
        lead_ids=[lead_1.id, lead_2.id],
    )
    segment = await svc.create(tenant_id=TENANT_A, dto=dto, session=db_session)

    # Flush so the segment is readable in the same session
    await db_session.flush()

    lead_ids, total, truncated = await svc.resolve(
        tenant_id=TENANT_A,
        segment_id=segment.id,
        session=db_session,
    )

    assert total == 2
    assert not truncated
    assert set(lead_ids) == {lead_1.id, lead_2.id}
    # Verify LeadQueryPort was NOT called (static short-circuit)
    svc._lead_query_port.list_lead_ids_matching.assert_not_called()  # type: ignore[attr-defined]


async def test_segment_create_dynamic_requires_filter_dsl() -> None:
    """DYNAMIC sin filter_dsl → Pydantic ValidationError."""
    with pytest.raises(ValidationError):
        SegmentCreate(
            name="Dinamico sin filtro",
            segment_type=SegmentType.DYNAMIC,
            # filter_dsl omitido — requerido para DYNAMIC
        )


async def test_segment_resolve_static_respects_limit(db_session: AsyncSession) -> None:
    """resolve() STATIC con limit < total devuelve truncated=True."""
    # Seed 5 leads
    leads = [_make_lead(TENANT_A) for _ in range(5)]
    db_session.add_all(leads)
    await db_session.flush()

    svc = _build_service()
    dto = SegmentCreate(
        name="Segmento truncate test",
        segment_type=SegmentType.STATIC,
        lead_ids=[l.id for l in leads],
    )
    segment = await svc.create(tenant_id=TENANT_A, dto=dto, session=db_session)
    await db_session.flush()

    capped, total, truncated = await svc.resolve(
        tenant_id=TENANT_A,
        segment_id=segment.id,
        limit=3,
        session=db_session,
    )
    assert total == 5
    assert len(capped) == 3
    assert truncated is True
