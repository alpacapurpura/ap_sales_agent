"""DB-seed fixture for eval simulator runs (T-3).

Materialises a Story-A ``TenantContext`` (loaded from
``backend/tests/fixtures/eval/tenants/``) into real Postgres rows with
deterministic UUID5 + soft-delete teardown. Reusable across the 5
archetypes via ``archetype_slug`` parametrisation.

Decisiones:
- D2 (spec): ``tenant_id = uuid5(NAMESPACE_DNS, f"eval-{slug}")`` deterministic.
- §2.6 (arch): is_eval_synthetic marker via ``eval_synthetic_tenants`` lookup
  table (Opción B). NO column ``is_eval_synthetic`` en tablas business —
  costo migration de +5 tablas sin ROI; lookup table escala.
- Teardown: soft-delete via ``deleted_at = utc_now()`` (NUNCA hard DELETE).
- Idempotent upsert: si la row existe, se restaura (``deleted_at = None``).

Tenant isolation (``.claude/rules/tenant-isolation.md``):
- Cada query DB filtra ``tenant_id`` explícito.
- TenantContext de Story A es read-only — fixture NO muta YAML.

Anti-duplication §0:
- Reusa ``TenantModel``, ``PersonalityProfileModel``, ``ProductModel``,
  ``BuyerPersonaModel``, ``EvalSyntheticTenantModel`` desde producción.
- Llama ``PersonalityCompiler.compile()`` desde brand domain para generar
  ``system_instruction`` (sin re-implementar local).
- NO mirror DDL, NO test-only ORM models.

Spanish neutro: mensajes structlog en español neutro latam
(``.claude/rules/spanish-text.md``).
"""

from __future__ import annotations

import uuid
from typing import Any
from uuid import UUID

import pytest
import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.shared.domain.datetime_utils import utc_now
from tests.fixtures.eval.tenants.loader import (
    ARCHETYPE_SLUGS,
    TenantContext,
    load_eval_tenant,
)

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Namespace para uuid5 determinístico (D2).
_EVAL_TENANT_NAMESPACE: uuid.UUID = uuid.NAMESPACE_DNS


def _eval_tenant_id(archetype_slug: str) -> UUID:
    """Derivar tenant_id determinístico (D2 idempotencia H2).

    Args:
        archetype_slug: One of the 5 ratified slugs.

    Returns:
        UUID — idempotente across runs: ``uuid5(NAMESPACE_DNS, f"eval-{slug}")``.
    """
    return uuid.uuid5(_EVAL_TENANT_NAMESPACE, f"eval-{archetype_slug}")


# ---------------------------------------------------------------------------
# Internal seed helpers
# ---------------------------------------------------------------------------


def _upsert_lookup(
    db: Session,
    tenant_id: UUID,
    archetype_slug: str,
) -> None:
    """Upsert row en ``eval_synthetic_tenants`` lookup table.

    Si existe con ``deleted_at`` seteado, restaura a ``None`` (idempotencia teardown).
    Si no existe, inserta.
    """
    from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_synthetic_tenants import (
        EvalSyntheticTenantModel,
    )

    row = db.execute(
        select(EvalSyntheticTenantModel).where(
            EvalSyntheticTenantModel.tenant_id == tenant_id,
        ),
    ).scalar_one_or_none()

    if row is None:
        row = EvalSyntheticTenantModel(
            tenant_id=tenant_id,
            archetype_slug=archetype_slug,
            seeded_at=utc_now(),
        )
        db.add(row)
        logger.info(
            "eval_synthetic_tenant_lookup_insertado",
            tenant_id=str(tenant_id),
            archetype_slug=archetype_slug,
        )
    elif row.deleted_at is not None:
        row.deleted_at = None
        row.seeded_at = utc_now()
        logger.info(
            "eval_synthetic_tenant_lookup_restaurado",
            tenant_id=str(tenant_id),
            archetype_slug=archetype_slug,
        )

    db.flush()


def _upsert_tenant(
    db: Session,
    tenant_id: UUID,
    archetype_slug: str,
    ctx: TenantContext,
) -> None:
    """Upsert row en ``tenants`` table.

    Almacena ``brand_settings`` en ``config_json`` para que
    ``BrandRepository.get_settings()`` retorne datos correctos al
    construir la identity del agente.

    Currency: derivada de ``ctx.pricing.currency`` (NO hardcoded 'USD'
    per ``.claude/rules/currency-handling.md``).
    """
    from src.modules.iam.infrastructure.models.tenant_model import TenantModel

    tenant = db.execute(
        select(TenantModel).where(TenantModel.id == tenant_id),
    ).scalar_one_or_none()

    currency: str = ctx.pricing.get("currency", "PEN")  # seed data en PEN per Q3
    brand_name: str = ctx.brand.get("identity", {}).get("brand_name", f"eval-{archetype_slug}")
    config: dict[str, Any] = {"brand_settings": ctx.brand}

    if tenant is None:
        tenant = TenantModel(
            id=tenant_id,
            name=brand_name,
            slug=f"eval-{archetype_slug}",
            config_json=config,
            default_currency=currency,
            timezone="UTC",
        )
        db.add(tenant)
        logger.info(
            "eval_tenant_insertado",
            tenant_id=str(tenant_id),
            archetype_slug=archetype_slug,
            brand_name=brand_name,
            currency=currency,
        )
    else:
        # Actualizar brand settings (re-seed idempotente).
        tenant.config_json = config
        tenant.default_currency = currency
        logger.info(
            "eval_tenant_actualizado",
            tenant_id=str(tenant_id),
            archetype_slug=archetype_slug,
        )

    db.flush()


def _upsert_personality_profile(
    db: Session,
    tenant_id: UUID,
    ctx: TenantContext,
) -> UUID:
    """Upsert row en ``personality_profiles`` table.

    Compila ``system_instruction`` via ``PersonalityCompiler.compile()``
    para que ``TenantKnowledgeBuilder.build_brand_voice()`` retorne voz
    compilada correcta (5-block instruction slot 5 cache prefix).

    Returns:
        UUID del PersonalityProfileModel upserted.
    """
    from src.modules.brand.domain.personality import (
        LinguisticPatterns,
        PersonalityCompiler,
        PersonalityDimensions,
        SampleExchange,
    )
    from src.modules.brand.infrastructure.models.personality_model import (
        PersonalityProfileModel,
    )

    # Buscar perfil activo existente para este tenant (sin offer_id/avatar_id).
    existing = db.execute(
        select(PersonalityProfileModel).where(
            PersonalityProfileModel.tenant_id == tenant_id,
            PersonalityProfileModel.offer_id.is_(None),
            PersonalityProfileModel.avatar_id.is_(None),
            PersonalityProfileModel.deleted_at.is_(None),
        ),
    ).scalar_one_or_none()

    # Extraer 3 pilares del YAML.
    pp_raw: dict[str, Any] = ctx.personality_profile
    dims_raw: dict[str, Any] = pp_raw.get("dimensions", {})
    patterns_raw: dict[str, Any] = pp_raw.get("linguistic_patterns", {})
    exchanges_raw: list[dict[str, Any]] = pp_raw.get("sample_exchanges", [])

    # Construir Pydantic objects para compilador.
    dimensions = PersonalityDimensions(**dims_raw)
    patterns = LinguisticPatterns(**patterns_raw)
    exchanges = [SampleExchange(**ex) for ex in exchanges_raw]

    # Compilar system_instruction (5-block).
    system_instruction = PersonalityCompiler.compile(dimensions, patterns, exchanges)

    profile_name: str = pp_raw.get("tenant_slug", f"eval-{ctx.archetype_slug}-profile")

    if existing is None:
        profile_id = uuid.uuid4()
        profile = PersonalityProfileModel(
            id=profile_id,
            tenant_id=tenant_id,
            name=profile_name,
            profile_type="preset",
            is_active=True,
            dimensions=dims_raw,
            linguistic_patterns=patterns_raw,
            sample_exchanges=exchanges_raw,
            negative_constraints=[],
            system_instruction=system_instruction,
        )
        db.add(profile)
        logger.info(
            "eval_personality_profile_insertado",
            tenant_id=str(tenant_id),
            profile_id=str(profile_id),
        )
    else:
        # Actualizar campos de pilares + system_instruction.
        existing.dimensions = dims_raw
        existing.linguistic_patterns = patterns_raw
        existing.sample_exchanges = exchanges_raw
        existing.system_instruction = system_instruction
        existing.is_active = True
        profile_id = existing.id
        logger.info(
            "eval_personality_profile_actualizado",
            tenant_id=str(tenant_id),
            profile_id=str(profile_id),
        )

    db.flush()
    return profile_id


def _upsert_offers(
    db: Session,
    tenant_id: UUID,
    ctx: TenantContext,
) -> list[UUID]:
    """Upsert rows en ``products`` table desde ``ctx.offer_ladder.raw["offers"]``.

    Cada offer usa ``uuid5`` sobre ``f"eval-{tenant_id}-offer-{level}"`` para
    ser idempotente. Currency derivada de ``ctx.pricing.currency``.

    Returns:
        Lista de offer UUIDs insertados/actualizados.
    """
    from src.modules.offer.infrastructure.models.product_model import ProductModel

    offers_raw: list[dict[str, Any]] = ctx.offer_ladder.raw.get("offers", [])
    currency: str = ctx.pricing.get("currency", "PEN")
    upserted_ids: list[UUID] = []

    for offer_raw in offers_raw:
        level: str = str(offer_raw.get("level", "L0"))
        offer_id = uuid.uuid5(
            _EVAL_TENANT_NAMESPACE,
            f"eval-{tenant_id!s}-offer-{level}",
        )

        # Nombre público de la oferta.
        identity: dict[str, Any] = offer_raw.get("identity", {})
        name: str = identity.get("name", f"eval offer {level}")

        # Archetype + value_level desde YAML.
        archetype: str = offer_raw.get("archetype", "SERVICIO")
        value_level: str = offer_raw.get("value_level", "")

        existing_offer = db.execute(
            select(ProductModel).where(
                ProductModel.id == offer_id,
                ProductModel.tenant_id == tenant_id,
            ),
        ).scalar_one_or_none()

        if existing_offer is None:
            product = ProductModel(
                id=offer_id,
                tenant_id=tenant_id,
                name=name,
                status="active",
                archetype=archetype,
                value_level=value_level,
                currency=currency,
                is_lead_magnet=(value_level in {"lead_magnet", "L0", "LEAD_MAGNET"}),
                metadata_info={"eval_level": level, "archetype_slug": ctx.archetype_slug},
            )
            db.add(product)
            logger.info(
                "eval_offer_insertado",
                offer_id=str(offer_id),
                tenant_id=str(tenant_id),
                level=level,
                archetype=archetype,
            )
        else:
            # Restaurar si soft-deleted; actualizar nombre/currency.
            existing_offer.deleted_at = None
            existing_offer.name = name
            existing_offer.currency = currency
            existing_offer.is_lead_magnet = value_level in {"lead_magnet", "L0", "LEAD_MAGNET"}
            logger.info(
                "eval_offer_actualizado",
                offer_id=str(offer_id),
                tenant_id=str(tenant_id),
                level=level,
            )

        upserted_ids.append(offer_id)

    db.flush()
    return upserted_ids


def _upsert_buyer_personas(
    db: Session,
    tenant_id: UUID,
    ctx: TenantContext,
) -> list[UUID]:
    """Upsert rows en ``buyer_personas`` table desde ``ctx.buyer_personas``.

    Usa ``uuid5`` sobre ``f"eval-{tenant_id}-persona-{name}"`` para idempotencia.
    ``user_id`` se pone al mismo valor que ``tenant_id`` (eval-only synthetic,
    no hay usuario real). ``scope = "GLOBAL"`` para que el agente los detecte.

    Returns:
        Lista de buyer_persona UUIDs insertados/actualizados.
    """
    from src.modules.brand.infrastructure.models.buyer_persona_model import (
        BuyerPersonaModel,
    )

    personas_raw: list[dict[str, Any]] = ctx.buyer_personas.get("personas", [])
    upserted_ids: list[UUID] = []

    for i, persona_raw in enumerate(personas_raw):
        name: str = persona_raw.get("name", f"persona-{i}")
        persona_id = uuid.uuid5(
            _EVAL_TENANT_NAMESPACE,
            f"eval-{tenant_id!s}-persona-{name}",
        )

        existing = db.execute(
            select(BuyerPersonaModel).where(
                BuyerPersonaModel.id == persona_id,
                BuyerPersonaModel.tenant_id == tenant_id,
            ),
        ).scalar_one_or_none()

        tagline: str = persona_raw.get("tagline", "")
        demographics: dict[str, Any] = {
            k: persona_raw.get(k)
            for k in ("age", "role", "location", "income_range_pen", "education")
            if persona_raw.get(k) is not None
        }
        pain_points: list[Any] = persona_raw.get("pain_points", [])
        desires: list[Any] = persona_raw.get("desires", [])
        is_primary: bool = i == 0  # primera persona = primaria

        if existing is None:
            persona = BuyerPersonaModel(
                id=persona_id,
                tenant_id=tenant_id,
                user_id=tenant_id,  # eval-only synthetic: user_id = tenant_id
                name=name,
                tagline=tagline,
                scope="GLOBAL",
                is_primary=is_primary,
                demographics=demographics,
                psychographics={},
                pain_points=pain_points if isinstance(pain_points, list) else [],
                desires=desires if isinstance(desires, list) else [],
                buyer_journey={},
                purchase_triggers=[],
                anti_patterns=[],
                completeness_score=0.0,
            )
            db.add(persona)
            logger.info(
                "eval_buyer_persona_insertado",
                persona_id=str(persona_id),
                tenant_id=str(tenant_id),
                persona_name=name,
            )
        else:
            existing.deleted_at = None
            existing.name = name
            existing.tagline = tagline
            existing.is_primary = is_primary
            logger.info(
                "eval_buyer_persona_actualizado",
                persona_id=str(persona_id),
                tenant_id=str(tenant_id),
                persona_name=name,
            )

        upserted_ids.append(persona_id)

    db.flush()
    return upserted_ids


# ---------------------------------------------------------------------------
# Teardown helper
# ---------------------------------------------------------------------------


def _soft_delete_lookup(db: Session, tenant_id: UUID) -> None:
    """Marcar lookup row como deleted para teardown idempotente.

    Soft-delete ÚNICAMENTE el marcador en ``eval_synthetic_tenants``.
    Las filas en tablas business (tenants, products, etc.) NO se borran
    aquí — quedan para facilitar debug post-run. Las queries de Streamlit
    prod filtran via ``eval_synthetic_tenants.deleted_at IS NULL``.
    """
    from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_synthetic_tenants import (
        EvalSyntheticTenantModel,
    )

    try:
        row = db.execute(
            select(EvalSyntheticTenantModel).where(
                EvalSyntheticTenantModel.tenant_id == tenant_id,
            ),
        ).scalar_one_or_none()
        if row is not None and row.deleted_at is None:
            row.deleted_at = utc_now()
            db.commit()
            logger.info(
                "eval_synthetic_tenant_teardown_completado",
                tenant_id=str(tenant_id),
            )
    except Exception as exc:  # noqa: BLE001 — teardown best-effort
        logger.warning(
            "eval_synthetic_tenant_teardown_fallido",
            tenant_id=str(tenant_id),
            error=str(exc),
        )
        import contextlib

        with contextlib.suppress(Exception):
            db.rollback()


# ---------------------------------------------------------------------------
# Public fixture
# ---------------------------------------------------------------------------


def seed_eval_tenant(
    db: Session,
    archetype_slug: str,
) -> tuple[UUID, TenantContext]:
    """Sembrar un tenant eval en la DB y retornar (tenant_id, TenantContext).

    Función pública reutilizable por tests síncronos que ya tienen sesión DB.
    El ciclo de vida (commit + teardown) es responsabilidad del llamador.

    Args:
        db: Sesión DB activa (caller gestiona lifecycle).
        archetype_slug: Uno de los 5 slugs ratificados.

    Returns:
        Tuple ``(tenant_id, TenantContext)`` — tenant_id determinístico UUID5.

    Raises:
        ValueError: Si ``archetype_slug`` no está en ``ARCHETYPE_SLUGS``.
        FileNotFoundError: Si los YAML de Story A faltan (precondición).
    """
    if archetype_slug not in ARCHETYPE_SLUGS:
        valid = list(ARCHETYPE_SLUGS)
        msg = f"archetype_slug {archetype_slug!r} no encontrado. Válidos: {valid}"
        raise ValueError(msg)

    ctx = load_eval_tenant(archetype_slug)
    tenant_id = _eval_tenant_id(archetype_slug)

    # 1. Lookup table (marcador).
    _upsert_lookup(db, tenant_id, archetype_slug)

    # 2. Tenant row (config_json con brand_settings + currency).
    _upsert_tenant(db, tenant_id, archetype_slug, ctx)

    # 3. PersonalityProfile con system_instruction compilado.
    _upsert_personality_profile(db, tenant_id, ctx)

    # 4. Offers (products) de offer_ladder.
    _upsert_offers(db, tenant_id, ctx)

    # 5. Buyer personas.
    _upsert_buyer_personas(db, tenant_id, ctx)

    db.commit()

    logger.info(
        "eval_tenant_sembrado_completo",
        tenant_id=str(tenant_id),
        archetype_slug=archetype_slug,
    )

    return tenant_id, ctx


@pytest.fixture
def eval_tenant_seeded() -> Any:
    """Fixture pytest para sembrar un tenant eval en la DB.

    Retorna un callable ``seed(archetype_slug) -> (UUID, TenantContext)``
    que inserta filas DB + registra en ``eval_synthetic_tenants`` lookup.

    Teardown: soft-deletes el row en ``eval_synthetic_tenants`` (marker) al
    finalizar la sesión. Las tablas business quedan para facilitar debug.

    Returns:
        Callable que acepta ``archetype_slug: str`` y retorna
        ``(tenant_id: UUID, ctx: TenantContext)``.

    Raises:
        ValueError: Si ``archetype_slug`` no en ``ARCHETYPE_SLUGS``.
        FileNotFoundError: Si YAML de Story A falta (precondición).

    Note:
        - Tenant isolation: queries con ``tenant_id`` explícito en cada upsert.
        - Idempotente: re-run safe (upsert pattern, no duplicate inserts).
        - Soft-delete teardown: ``eval_synthetic_tenants.deleted_at = utc_now()``.
        - No depende de ``visionarias_tenant_session`` — abre sesión propia.
    """
    from src.core.database import SessionLocal

    db: Session = SessionLocal()
    seeded_ids: list[UUID] = []

    def _seed(archetype_slug: str) -> tuple[UUID, TenantContext]:
        tenant_id, ctx = seed_eval_tenant(db, archetype_slug)
        seeded_ids.append(tenant_id)
        return tenant_id, ctx

    yield _seed

    # Teardown: soft-delete marcadores en eval_synthetic_tenants.
    for tid in seeded_ids:
        _soft_delete_lookup(db, tid)

    db.close()
