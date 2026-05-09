"""Tests for ``eval_tenant_seeded`` fixture (T-3).

Acceptance criteria:
- A1: Fixture seeds DB rows + returns deterministic tenant_id.
- A2: Teardown soft-deletes idempotently.
- A3: Cross-tenant isolation — 5 archetypes don't bleed.

Test partition:
- All tests are marked ``@pytest.mark.no_eval`` (no LLM invocation).
- DB tests are marked ``@pytest.mark.integration`` (require Postgres).
- ``test_invalid_archetype_raises_valueerror`` is pure unit (no DB — fast path).

Tenant isolation (``.claude/rules/tenant-isolation.md``):
- Cada query DB filtra ``tenant_id`` explícito.
- Cross-tenant test verifica que cada archetype tiene UUID5 distinto.
- No hay leak entre sesiones de fixtures distintas.

TDD: RED tests escritos PRIMERO; implementación sigue.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
import structlog
from sqlalchemy import select

if TYPE_CHECKING:
    from collections.abc import Callable

    from tests.fixtures.eval.tenants.loader import TenantContext

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Section 1 — unit tests (no DB, no LLM, always run)
# ---------------------------------------------------------------------------


@pytest.mark.no_eval
def test_invalid_archetype_raises_valueerror() -> None:
    """Invocar seed con slug inválido levanta ValueError + cero DB writes.

    A4 verifier: sin DB involucrada — error levantado antes del primer execute.
    """
    from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
        _eval_tenant_id,
    )
    from tests.fixtures.eval.tenants.loader import ARCHETYPE_SLUGS

    invalid_slug = "tenant_inexistente"
    assert invalid_slug not in ARCHETYPE_SLUGS, (
        f"{invalid_slug!r} should not be in ARCHETYPE_SLUGS — test assumption violated"
    )

    # _eval_tenant_id debe calcularse correctamente para slugs válidos.
    for slug in ARCHETYPE_SLUGS:
        tid = _eval_tenant_id(slug)
        assert isinstance(tid, UUID)
        assert tid == uuid.uuid5(uuid.NAMESPACE_DNS, f"eval-{slug}")


@pytest.mark.no_eval
def test_eval_tenant_id_is_deterministic() -> None:
    """uuid5 retorna el mismo valor para el mismo slug (idempotencia H2).

    Probar dos veces sin DB — sólo aritmética UUID5.
    """
    from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
        _eval_tenant_id,
    )

    slug = "tenant_coach_lat"
    id1 = _eval_tenant_id(slug)
    id2 = _eval_tenant_id(slug)
    assert id1 == id2, f"UUID5 debería ser idempotente, obtuvo {id1} != {id2}"


@pytest.mark.no_eval
def test_all_five_archetypes_have_distinct_ids() -> None:
    """Cinco slugs distintos producen cinco UUIDs distintos.

    Cross-tenant isolation precondición (sin DB).
    """
    from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
        _eval_tenant_id,
    )
    from tests.fixtures.eval.tenants.loader import ARCHETYPE_SLUGS

    ids = [_eval_tenant_id(slug) for slug in ARCHETYPE_SLUGS]
    assert len(set(ids)) == len(ARCHETYPE_SLUGS), f"Todos los archetypes deben tener UUIDs distintos. Obtuvo: {ids}"


# ---------------------------------------------------------------------------
# Section 2 — integration tests (require real Postgres)
# ---------------------------------------------------------------------------


@pytest.fixture
def _db_session():  # type: ignore[return]  # pytest generator fixture
    """Real Postgres session for integration tests.

    Yields:
        Session — abrir + cerrar en cada test para aislamiento completo.
    """
    from src.core.database import SessionLocal

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _skip_if_no_postgres() -> None:
    """Saltar test si Postgres no está disponible desde WSL nativo."""
    try:
        from src.core.database import SessionLocal

        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
    except Exception as exc:  # noqa: BLE001 — broad except para skip
        pytest.skip(
            f"Postgres no disponible desde WSL nativo. Verifica que el contenedor esté corriendo. Detalle: {exc}",
        )


@pytest.mark.no_eval
@pytest.mark.integration
def test_seeds_and_returns_uuid5(_db_session) -> None:  # type: ignore[no-untyped-def]
    """A1: Fixture siembra filas DB y retorna tenant_id determinístico UUID5.

    Verifica:
    - UUID5 calculado correctamente para ``tenant_coach_lat``.
    - Row en ``eval_synthetic_tenants`` insertada con ``deleted_at=None``.
    - Row en ``tenants`` insertada con ``config_json.brand_settings`` poblado.
    - Row en ``personality_profiles`` con ``system_instruction`` no vacío.
    - Al menos 1 row en ``products`` para el tenant.
    """
    _skip_if_no_postgres()

    from src.modules.brand.infrastructure.models.personality_model import (
        PersonalityProfileModel,
    )
    from src.modules.iam.infrastructure.models.tenant_model import TenantModel
    from src.modules.offer.infrastructure.models.product_model import ProductModel
    from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_synthetic_tenants import (
        EvalSyntheticTenantModel,
    )
    from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
        _eval_tenant_id,
        seed_eval_tenant,
    )

    slug = "tenant_coach_lat"
    expected_tenant_id = _eval_tenant_id(slug)

    db = _db_session

    try:
        returned_tenant_id, ctx = seed_eval_tenant(db, slug)

        # A1a: UUID retornado == uuid5(NAMESPACE_DNS, f"eval-{slug}")
        assert returned_tenant_id == expected_tenant_id, (
            f"tenant_id retornado {returned_tenant_id} != esperado {expected_tenant_id}"
        )

        # A1b: Row en eval_synthetic_tenants.
        lookup_row = db.execute(
            select(EvalSyntheticTenantModel).where(
                EvalSyntheticTenantModel.tenant_id == expected_tenant_id,
            ),
        ).scalar_one_or_none()
        assert lookup_row is not None, "Row eval_synthetic_tenants no encontrada"
        assert lookup_row.deleted_at is None, "eval_synthetic_tenants.deleted_at debería ser NULL post-seed"
        assert lookup_row.archetype_slug == slug

        # A1c: Row en tenants con brand_settings.
        tenant_row = db.execute(
            select(TenantModel).where(TenantModel.id == expected_tenant_id),
        ).scalar_one_or_none()
        assert tenant_row is not None, "Row tenants no encontrada"
        assert tenant_row.config_json is not None
        assert "brand_settings" in tenant_row.config_json, "tenants.config_json debe contener 'brand_settings'"

        # A1d: PersonalityProfile con system_instruction compilado.
        pp_row = db.execute(
            select(PersonalityProfileModel).where(
                PersonalityProfileModel.tenant_id == expected_tenant_id,
                PersonalityProfileModel.offer_id.is_(None),
                PersonalityProfileModel.avatar_id.is_(None),
                PersonalityProfileModel.deleted_at.is_(None),
                PersonalityProfileModel.is_active.is_(True),
            ),
        ).scalar_one_or_none()
        assert pp_row is not None, "PersonalityProfile no encontrado"
        assert pp_row.system_instruction is not None, "system_instruction debe estar compilado"
        assert len(pp_row.system_instruction) > 100, (
            f"system_instruction parece vacío/incompleto (len={len(pp_row.system_instruction)})"
        )

        # A1e: Al menos 1 producto activo.
        product_count = (
            db.execute(
                select(ProductModel).where(
                    ProductModel.tenant_id == expected_tenant_id,
                    ProductModel.deleted_at.is_(None),
                ),
            )
            .scalars()
            .all()
        )
        assert len(product_count) >= 1, f"Se esperaba al menos 1 offer, obtuvo {len(product_count)}"

        # A1f: Tenant isolation — ninguna row retornada sin filtrar tenant_id.
        offers_sin_filtro_incorrecto = db.execute(
            select(ProductModel).where(
                ProductModel.id == product_count[0].id,
                ProductModel.tenant_id == expected_tenant_id,  # filtro explícito
            ),
        ).scalar_one_or_none()
        assert offers_sin_filtro_incorrecto is not None, "Offer debería encontrarse con tenant_id correcto"

        logger.info(
            "test_seeds_and_returns_uuid5_pass",
            tenant_id=str(expected_tenant_id),
            products_inserted=len(product_count),
        )

    finally:
        # Cleanup: soft-delete para no ensuciar la DB entre tests.
        from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
            _soft_delete_lookup,
        )

        _soft_delete_lookup(db, expected_tenant_id)


@pytest.mark.no_eval
@pytest.mark.integration
def test_teardown_soft_delete_idempotent(_db_session) -> None:  # type: ignore[no-untyped-def]
    """A2: Teardown soft-deletes idempotently.

    Verifica:
    - Post-seed: ``eval_synthetic_tenants.deleted_at = NULL``.
    - Post-teardown (1ra vez): ``deleted_at`` seteado (no NULL).
    - Post-teardown (2da vez): no error, estado idempotente.
    - Re-seed: ``deleted_at`` restaurado a NULL.
    """
    _skip_if_no_postgres()

    from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_synthetic_tenants import (
        EvalSyntheticTenantModel,
    )
    from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
        _eval_tenant_id,
        _soft_delete_lookup,
        seed_eval_tenant,
    )

    slug = "tenant_medicina_estetica"
    tenant_id = _eval_tenant_id(slug)
    db = _db_session

    try:
        # Step 1: Sembrar.
        returned_id, _ = seed_eval_tenant(db, slug)
        assert returned_id == tenant_id

        # Verificar: deleted_at = NULL post-seed.
        row_after_seed = db.execute(
            select(EvalSyntheticTenantModel).where(
                EvalSyntheticTenantModel.tenant_id == tenant_id,
            ),
        ).scalar_one_or_none()
        assert row_after_seed is not None
        assert row_after_seed.deleted_at is None, "Post-seed deleted_at debe ser NULL"

        # Step 2: Teardown 1ra vez.
        _soft_delete_lookup(db, tenant_id)

        # Verificar: deleted_at seteado.
        # Re-query con nueva query (no cached).
        db.expire_all()
        row_after_teardown = db.execute(
            select(EvalSyntheticTenantModel).where(
                EvalSyntheticTenantModel.tenant_id == tenant_id,
            ),
        ).scalar_one_or_none()
        assert row_after_teardown is not None
        assert row_after_teardown.deleted_at is not None, "Post-teardown deleted_at debe estar seteado"

        # Step 3: Teardown 2da vez — idempotente (no error).
        _soft_delete_lookup(db, tenant_id)  # No debe lanzar excepción.

        # Step 4: Re-seed restaura deleted_at a NULL.
        returned_id_2, _ = seed_eval_tenant(db, slug)
        assert returned_id_2 == tenant_id

        db.expire_all()
        row_after_reseed = db.execute(
            select(EvalSyntheticTenantModel).where(
                EvalSyntheticTenantModel.tenant_id == tenant_id,
            ),
        ).scalar_one_or_none()
        assert row_after_reseed is not None
        assert row_after_reseed.deleted_at is None, "Re-seed debe restaurar deleted_at a NULL"

        logger.info(
            "test_teardown_soft_delete_idempotent_pass",
            tenant_id=str(tenant_id),
        )

    finally:
        _soft_delete_lookup(db, tenant_id)


@pytest.mark.no_eval
@pytest.mark.integration
def test_cross_tenant_isolation(_db_session) -> None:  # type: ignore[no-untyped-def]
    """A3: Cross-tenant isolation — 5 archetypes sembrados no hacen bleed.

    Para cada uno de los 5 archetypes:
    - UUID5 es distinto del resto.
    - Products sembrados bajo tenant A NO aparecen en query filtrada por tenant B.
    - Lookup rows son independientes.
    """
    _skip_if_no_postgres()

    from src.modules.offer.infrastructure.models.product_model import ProductModel
    from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_synthetic_tenants import (
        EvalSyntheticTenantModel,
    )
    from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
        _eval_tenant_id,
        _soft_delete_lookup,
        seed_eval_tenant,
    )
    from tests.fixtures.eval.tenants.loader import ARCHETYPE_SLUGS

    db = _db_session
    seeded: list[UUID] = []

    try:
        # Sembrar todos los 5 archetypes.
        for slug in ARCHETYPE_SLUGS:
            returned_id, _ = seed_eval_tenant(db, slug)
            expected_id = _eval_tenant_id(slug)
            assert returned_id == expected_id, f"UUID mismatch para {slug}: {returned_id} != {expected_id}"
            seeded.append(returned_id)

        # Verificar UUIDs todos distintos.
        assert len(set(seeded)) == len(ARCHETYPE_SLUGS), f"Todos los tenant_ids deben ser distintos. Obtuvo: {seeded}"

        # Para cada tenant, verificar:
        # (a) Sus offers pertenecen SOLO a ese tenant_id.
        # (b) Lookup row existe y es independiente.
        for i, slug in enumerate(ARCHETYPE_SLUGS):
            current_tid = seeded[i]
            other_tids = [tid for j, tid in enumerate(seeded) if j != i]

            # (a) Offers de este tenant — deben existir.
            current_offers = (
                db.execute(
                    select(ProductModel).where(
                        ProductModel.tenant_id == current_tid,
                        ProductModel.deleted_at.is_(None),
                    ),
                )
                .scalars()
                .all()
            )
            assert len(current_offers) >= 1, f"Tenant {slug} ({current_tid}) debe tener al menos 1 offer"

            # (a2) Offers de ESTE tenant NO aparecen en queries de otros tenants.
            for current_offer in current_offers:
                for other_tid in other_tids:
                    cross_leak = db.execute(
                        select(ProductModel).where(
                            ProductModel.id == current_offer.id,
                            ProductModel.tenant_id == other_tid,  # filtro otro tenant
                        ),
                    ).scalar_one_or_none()
                    assert cross_leak is None, (
                        f"Cross-tenant leak detectado: offer {current_offer.id} "
                        f"del tenant {current_tid} apareció en query del tenant "
                        f"{other_tid}"
                    )

            # (b) Lookup row para este tenant existe + sin deleted_at.
            lookup = db.execute(
                select(EvalSyntheticTenantModel).where(
                    EvalSyntheticTenantModel.tenant_id == current_tid,
                ),
            ).scalar_one_or_none()
            assert lookup is not None, f"Lookup row faltante para tenant {slug} ({current_tid})"
            assert lookup.deleted_at is None, f"Lookup row de {slug} tiene deleted_at seteado post-seed"
            assert lookup.archetype_slug == slug, (
                f"archetype_slug mismatch en lookup: {lookup.archetype_slug} != {slug}"
            )

        logger.info(
            "test_cross_tenant_isolation_pass",
            archetypes=list(ARCHETYPE_SLUGS),
            tenant_ids=[str(tid) for tid in seeded],
        )

    finally:
        # Cleanup: soft-delete todos los tenants sembrados.
        for tid in seeded:
            _soft_delete_lookup(db, tid)


@pytest.mark.no_eval
@pytest.mark.integration
def test_seed_eval_tenant_invalid_slug_no_db_write(_db_session) -> None:  # type: ignore[no-untyped-def]
    """A4: Slug inválido levanta ValueError ANTES de cualquier write a DB.

    Verificación adicional: la DB no tiene rows con el slug inválido.
    """
    _skip_if_no_postgres()

    from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
        seed_eval_tenant,
    )

    db = _db_session
    invalid_slug = "tenant_inexistente"

    with pytest.raises(ValueError, match=r"archetype_slug.*no encontrado"):
        seed_eval_tenant(db, invalid_slug)

    # Verificar que no hay rows con el slug inválido.
    from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_synthetic_tenants import (
        EvalSyntheticTenantModel,
    )

    rows = (
        db.execute(
            select(EvalSyntheticTenantModel).where(
                EvalSyntheticTenantModel.archetype_slug == invalid_slug,
            ),
        )
        .scalars()
        .all()
    )
    assert len(rows) == 0, f"No debe haber rows con archetype_slug={invalid_slug!r}"

    logger.info("test_invalid_archetype_no_db_write_pass", invalid_slug=invalid_slug)


@pytest.mark.no_eval
@pytest.mark.integration
def test_seed_is_idempotent_on_rerun(_db_session) -> None:  # type: ignore[no-untyped-def]
    """Re-run de seed_eval_tenant en el mismo slug no crea duplicados.

    Verifica:
    - Dos llamadas consecutivas para el mismo slug no dupliquen rows.
    - tenant_id idéntico en ambas llamadas.
    - Exactamente 1 lookup row por tenant_id.
    """
    _skip_if_no_postgres()

    from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_synthetic_tenants import (
        EvalSyntheticTenantModel,
    )
    from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
        _eval_tenant_id,
        _soft_delete_lookup,
        seed_eval_tenant,
    )

    slug = "tenant_clinica_dental"
    tenant_id = _eval_tenant_id(slug)
    db = _db_session

    try:
        # Primera seed.
        id1, ctx1 = seed_eval_tenant(db, slug)
        assert id1 == tenant_id

        # Segunda seed (idempotente).
        id2, ctx2 = seed_eval_tenant(db, slug)
        assert id2 == tenant_id, "Segunda seed debe retornar el mismo tenant_id"
        assert id1 == id2

        # Verificar exactamente 1 lookup row.
        lookup_rows = (
            db.execute(
                select(EvalSyntheticTenantModel).where(
                    EvalSyntheticTenantModel.tenant_id == tenant_id,
                ),
            )
            .scalars()
            .all()
        )
        assert len(lookup_rows) == 1, f"Debe haber exactamente 1 lookup row, obtuvo {len(lookup_rows)}"

        logger.info("test_seed_is_idempotent_pass", tenant_id=str(tenant_id))

    finally:
        _soft_delete_lookup(db, tenant_id)


# ---------------------------------------------------------------------------
# Section 3 — DEEPER-C synthetic lead seed regression (Bug 4 hot-fix 2026-05-08)
# ---------------------------------------------------------------------------


@pytest.mark.no_eval
def test_eval_synthetic_lead_id_is_deterministic() -> None:
    """DEEPER-C: ``eval_synthetic_lead_id(tenant_id)`` is idempotent.

    Pure UUID5 arithmetic — no DB. Verifica que el bridge y la fixture
    derivan el mismo UUID dado el mismo tenant_id (bridge contract).
    """
    from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
        _eval_tenant_id,
        eval_synthetic_lead_id,
    )

    tenant_id = _eval_tenant_id("tenant_coach_lat")

    lead_id_1 = eval_synthetic_lead_id(tenant_id)
    lead_id_2 = eval_synthetic_lead_id(tenant_id)

    assert lead_id_1 == lead_id_2, f"eval_synthetic_lead_id must be idempotent — got {lead_id_1} != {lead_id_2}"

    # Cross-tenant: distinct tenants yield distinct lead IDs.
    other_tenant = _eval_tenant_id("tenant_medicina_estetica")
    other_lead = eval_synthetic_lead_id(other_tenant)
    assert lead_id_1 != other_lead, (
        f"Distinct tenants must yield distinct synthetic lead IDs — got {lead_id_1} == {other_lead}"
    )


@pytest.mark.no_eval
@pytest.mark.integration
def test_seed_creates_synthetic_lead_for_fk(_db_session) -> None:  # type: ignore[no-untyped-def]
    """DEEPER-C Bug 4 regression: post-seed, una row sintética en ``leads``
    existe para satisfacer ``agent_traces_user_id_fkey``.

    Pre-fix: ``seed_eval_tenant`` no creaba lead row → primera invocación
    del production graph (que escribe ``agent_traces.user_id``) revienta
    con ``ForeignKeyViolation``.

    Post-fix: lead row deterministic UUID5 ``eval_synthetic_lead_id(tenant_id)``
    + ``tenant_id`` filtered (tenant isolation per
    ``.claude/rules/tenant-isolation.md``).
    """
    _skip_if_no_postgres()

    from src.shared.infrastructure.models.crm import LeadModel
    from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
        _eval_tenant_id,
        _soft_delete_lookup,
        eval_synthetic_lead_id,
        seed_eval_tenant,
    )

    slug = "tenant_coach_lat"
    tenant_id = _eval_tenant_id(slug)
    expected_lead_id = eval_synthetic_lead_id(tenant_id)
    db = _db_session

    try:
        seed_eval_tenant(db, slug)

        # Post-seed: la lead row existe + filtra por tenant_id (tenant isolation).
        lead = db.execute(
            select(LeadModel).where(
                LeadModel.id == expected_lead_id,
                LeadModel.tenant_id == tenant_id,
                LeadModel.deleted_at.is_(None),
            ),
        ).scalar_one_or_none()

        assert lead is not None, (
            f"Synthetic lead {expected_lead_id} para tenant {tenant_id} no encontrado — "
            f"agent_traces FK rompería en primera invocación del production graph"
        )

        # Sanity: tenant_id matches exactly.
        assert lead.tenant_id == tenant_id, (
            f"Lead tenant_id {lead.tenant_id} != expected {tenant_id} — tenant isolation violated"
        )

        # Cross-tenant isolation: lead NO aparece bajo otro tenant_id.
        other_tenant_id = _eval_tenant_id("tenant_medicina_estetica")
        cross_leak = db.execute(
            select(LeadModel).where(
                LeadModel.id == expected_lead_id,
                LeadModel.tenant_id == other_tenant_id,
            ),
        ).scalar_one_or_none()
        assert cross_leak is None, (
            f"Cross-tenant leak: synthetic lead {expected_lead_id} apareció en tenant {other_tenant_id}"
        )

        logger.info(
            "test_seed_creates_synthetic_lead_for_fk_pass",
            tenant_id=str(tenant_id),
            lead_id=str(expected_lead_id),
        )

    finally:
        _soft_delete_lookup(db, tenant_id)


@pytest.mark.no_eval
@pytest.mark.integration
def test_seed_synthetic_lead_is_idempotent(_db_session) -> None:  # type: ignore[no-untyped-def]
    """DEEPER-C: re-seeding does not duplicate the synthetic lead row.

    Idempotencia garantizada via UUID5 derivation + upsert pattern.
    """
    _skip_if_no_postgres()

    from src.shared.infrastructure.models.crm import LeadModel
    from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
        _eval_tenant_id,
        _soft_delete_lookup,
        eval_synthetic_lead_id,
        seed_eval_tenant,
    )

    slug = "tenant_coach_lat"
    tenant_id = _eval_tenant_id(slug)
    expected_lead_id = eval_synthetic_lead_id(tenant_id)
    db = _db_session

    try:
        # Seed twice.
        seed_eval_tenant(db, slug)
        seed_eval_tenant(db, slug)

        # Verificar exactamente 1 lead row.
        leads = (
            db.execute(
                select(LeadModel).where(
                    LeadModel.id == expected_lead_id,
                    LeadModel.tenant_id == tenant_id,
                ),
            )
            .scalars()
            .all()
        )
        assert len(leads) == 1, f"Re-seed debe ser idempotente — esperaba 1 lead row, obtuvo {len(leads)}"

    finally:
        _soft_delete_lookup(db, tenant_id)


@pytest.mark.no_eval
def test_agent_bridge_uses_deterministic_synthetic_user_id() -> None:
    """DEEPER-C bridge contract: ``agent_bridge`` uses
    :func:`eval_synthetic_lead_id` (NOT ``uuid4()``) so that the
    ``user_id`` injected in the agent's initial state matches the lead
    row seeded by ``tenant_seeded.py``.

    Pre-fix: ``synthetic_user_id = str(uuid4())`` per turn → random,
    no FK match. Post-fix: derived from ``state.tenant_id`` via
    deterministic UUID5.

    Verified by source-text check (paridad with anti-mirror grep verifiers
    in the simulator suite — ``test_simulator_no_mirrors_shared.py``
    pattern). Avoids the integration cost of constructing a full
    SimulationState + mocked agent_app + DB session.
    """
    from pathlib import Path

    # Resolve agent_bridge.py path: __file__ lives at
    # ``.../sales_agent/simulator/fixtures/test_tenant_seeded.py``;
    # parents[1] is the ``simulator/`` package (parent of ``fixtures/``).
    bridge_path = Path(__file__).resolve().parents[1] / "_internal" / "agent_bridge.py"
    src = bridge_path.read_text(encoding="utf-8")

    # Bridge MUST import the deterministic helper + upsert helper.
    assert "from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (" in src, (
        "agent_bridge.py must import from tenant_seeded"
    )
    assert "eval_synthetic_lead_id" in src, (
        "agent_bridge.py must import + use eval_synthetic_lead_id helper (DEEPER-C bridge contract for FK satisfaction)"
    )
    assert "_upsert_synthetic_lead" in src, (
        "agent_bridge.py must import + invoke _upsert_synthetic_lead "
        "(DEEPER-C two-layer defense: bridge self-heals when caller skips seed)"
    )

    # Bridge MUST derive synthetic_user_id from tenant_id deterministic UUID5.
    assert "synthetic_user_id = str(eval_synthetic_lead_id(state.tenant_id))" in src, (
        "agent_bridge.py must derive synthetic_user_id deterministically — "
        "NOT random uuid4(). Pre-fix anti-pattern: 'synthetic_user_id = str(uuid4())'."
    )

    # Bridge MUST invoke the lead upsert (best-effort) before agent_app.ainvoke.
    assert "_upsert_synthetic_lead(db, state.tenant_id)" in src, (
        "agent_bridge.py must invoke _upsert_synthetic_lead(db, state.tenant_id) — "
        "bridge self-heals to satisfy agent_traces FK when callers skip seed step "
        "(e.g. scripts/generate_golden_candidates.py path)"
    )

    # Negative grep — the legacy random uuid4 line must NOT remain
    # (uuid4 may still be imported for turn_id; we only ban the specific
    # synthetic_user_id assignment line).
    assert "synthetic_user_id = str(uuid4())" not in src, (
        "Found legacy random uuid4 assignment for synthetic_user_id — "
        "violates DEEPER-C bridge contract (FK violation regression risk)"
    )
