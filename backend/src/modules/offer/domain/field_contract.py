"""Offer FieldContract — declarative section map + overrides.

Post field-contract-platform refactor (Fase 04), this module declares
the semantic metadata Pydantic cannot express (section, copilot meta,
lifecycle, filters) and delegates derivation to
``src.shared.domain.field_contract``.

The derived :data:`OFFER_FIELD_CONTRACTS` is the single source of
truth for every consumer that needs to iterate Offer fields:

- ``offer/domain/copilot_editable_fields.py`` (proyección)
- ``offer/domain/extraction_section_map.py`` (proyección via
  ``fields_by_section``)
- ``copilot/domain/offer_fields.py`` (proyección)
- ``offer/api/offer_field_contract.py`` (HTTP snapshot)

Adding a new Offer Pydantic field requires two changes here:

1. Add ``"new_field": "section_slug"`` to :data:`OFFER_SECTION_MAP`.
2. (Optional) Add ``Override(...)`` in :data:`OFFER_FIELD_OVERRIDES`
   with ``human_question_es``, ``label_es``, ``priority``, etc.

That's it. All consumers pick it up via the registry. No more manual
drift across 5 paralell files.

Legacy exports (``FIELD_CONTRACT_REGISTRY``, ``FIELD_CONTRACT_SNAPSHOT``,
``PRICING_FIELD_CONTRACTS``, ``contracts_by_section``, ``FIELD_CONTRACT_VERSION``)
are preserved as aliases over the new derived registry for backward
compatibility with existing consumers (endpoint, tests).

See ``docs/refactors/field-contract-platform/DESIGN.md``.
"""

from __future__ import annotations

from src.modules.offer.domain.enums import OfferArchetype
from src.modules.offer.domain.offer import Offer
from src.shared.domain.field_contract import (
    FieldContract,
    FieldContractRegistrySnapshot,
    FieldStatus,
    PolymorphicVariantSpec,
    derive_contracts_from_pydantic,
    register_module_contracts,
)
from src.shared.domain.field_contract import FieldContractOverride as Override
from src.shared.domain.field_contract import fields_by_section as _shared_fields_by_section

# ---------------------------------------------------------------------------
# Ignore paths — system fields not user-facing
# ---------------------------------------------------------------------------

OFFER_IGNORE_PATHS: frozenset[str] = frozenset(
    {
        "id",
        "tenant_id",
        "archived_at",
        "deleted_at",
        "status",
        "metadata_info",
        "landing_page_config",
    }
)


# ---------------------------------------------------------------------------
# Section map — path → FE section slug
#
# Covers every Offer Pydantic path user-facing. Each entry is a
# conscious decision about where the field belongs in the FE layout.
#
# 21 FE section slugs (from section-catalog.ts / section_catalog.py):
# identity, strategy, psychology, promise, program_details,
# service_details, event_details, product_details, subscription_details,
# platform_details, location, instructors, value_stack, pricing,
# testimonials, portfolio, faq, gallery, resources, closing, knowledge
# ---------------------------------------------------------------------------

OFFER_SECTION_MAP: dict[str, str] = {
    # ── identity ────────────────────────────────────────────────────
    # Note: headline_promise / primary_outcome / time_to_value live here
    # (NOT in 'promise') to match legacy OFFER_FIELDS_BY_FE_SECTION grouping.
    # The FE 'identity' section covers offer's public identity + core promise.
    "internal_sku": "identity",
    "public_name": "identity",
    "archetype": "identity",
    "format_hint": "identity",
    "preset_id": "identity",
    "is_lead_magnet": "identity",
    "has_editions": "identity",
    "headline_promise": "identity",
    "primary_outcome": "identity",
    "time_to_value": "identity",
    # ── strategy ────────────────────────────────────────────────────
    "value_level": "strategy",
    "delivery_model": "strategy",
    "target_avatar_match": "strategy",
    "anti_avatar_keywords": "strategy",
    # ── promise (pitch fields, not identity) ────────────────────────
    "before_state": "promise",
    "after_state": "promise",
    "why_now": "promise",
    "measurable_outcomes": "promise",
    "requires_application": "promise",
    "min_financial_capacity": "promise",
    "prerequisites": "promise",
    # ── psychology ──────────────────────────────────────────────────
    "marketing_pain_points": "psychology",
    "marketing_desires": "psychology",
    "objections": "psychology",
    "cultural_trust_barriers": "psychology",
    "emotional_triggers": "psychology",
    "status_drivers": "psychology",
    "regret_scenarios": "psychology",
    # ── instructors ─────────────────────────────────────────────────
    "instructors": "instructors",
    "authority_positioning_for_sales": "instructors",
    "authority_notes": "instructors",
    # ── value_stack ─────────────────────────────────────────────────
    "deliverables": "value_stack",
    "includes_offers": "value_stack",
    "total_perceived_value_anchor": "value_stack",
    "stack_positioning_statement": "value_stack",
    # ── pricing ─────────────────────────────────────────────────────
    "pricing_options": "pricing",
    "price_pay_in_full": "pricing",
    "currency": "pricing",
    "tax_included": "pricing",
    "installments_available": "pricing",
    "accepted_payment_providers": "pricing",
    # ── closing ─────────────────────────────────────────────────────
    "guarantee_type": "closing",
    "guarantee_terms": "closing",
    "checkout_page_url": "closing",
    "calendar_type_id": "closing",
    "onboarding_action": "closing",
    "onboarding_url": "closing",
    "downsell_offer_id": "closing",
    "upsell_offer_id": "closing",
    "vsl_link": "closing",
    "refund_process_description": "closing",
    "urgency_drivers": "closing",
    "scarcity_reason_honest": "closing",
    "bonus_if_act_now": "closing",
    "final_push_copy": "closing",
    "support_duration_days": "closing",
    "access_duration": "closing",
    "access_duration_text": "closing",
    # specific_details.* paths — section derived per archetype via
    # _POLY_PREFIX_MAP below (PolymorphicVariantSpec). Sub-path overrides
    # live in OFFER_FIELD_OVERRIDES.
    #
    # platform_details.* paths (composable) ─────────────────────────────
    "platform_details.platform_features": "platform_details",
    "platform_details.platform_integrations": "platform_details",
    "platform_details.security_compliance": "platform_details",
    "platform_details.data_residency": "platform_details",
    "platform_details.uptime_guarantee": "platform_details",
    "platform_details.status_page_url": "platform_details",
    "platform_details.support_channels": "platform_details",
    "platform_details.api_available": "platform_details",
    "platform_details.api_docs_url": "platform_details",
    "platform_details.migration_tools": "platform_details",
    "platform_details.public_roadmap_url": "platform_details",
    "platform_details.changelog_url": "platform_details",
    "platform_details.ai_features_disclosure": "platform_details",
    "platform_details.data_export_capability": "platform_details",
}


def _build_polymorphic_prefix_map() -> dict[type, PolymorphicVariantSpec]:
    """Build the polymorphic map by importing variant classes.

    Each variant declares both the archetype filter and the FE section
    that its fields belong to. When two variants share a field name
    (e.g. ``start_date`` in Program + Event), two contracts are emitted
    — one per section — so archetype-aware consumers surface the
    correct section without runtime lookup.
    """
    from src.modules.offer.domain.details import (
        EventDetails,
        ProductDetails,
        ProgramDetails,
        ServiceDetails,
        SubscriptionDetails,
    )

    return {
        ProductDetails: PolymorphicVariantSpec(
            archetype_filter=(OfferArchetype.PRODUCTO.value,),
            section="product_details",
        ),
        ServiceDetails: PolymorphicVariantSpec(
            archetype_filter=(OfferArchetype.SERVICIO.value,),
            section="service_details",
        ),
        ProgramDetails: PolymorphicVariantSpec(
            archetype_filter=(OfferArchetype.PROGRAMA.value,),
            section="program_details",
        ),
        SubscriptionDetails: PolymorphicVariantSpec(
            archetype_filter=(OfferArchetype.MEMBRESIA.value,),
            section="subscription_details",
        ),
        EventDetails: PolymorphicVariantSpec(
            archetype_filter=(OfferArchetype.EXPERIENCIA.value,),
            section="event_details",
        ),
    }


# ---------------------------------------------------------------------------
# Field overrides — semantic metadata Pydantic cannot express
#
# Every override is optional. Omitting a field means defaults:
# - priority=0, is_required_semantic=False (unless structurally required),
#   can_propose=True, status=ACTIVE, no copilot meta.
#
# label_es: fallback for the copilot system prompt when the FE doesn't
# supply a label. We declare it for the fields that had labels in the
# pre-refactor OFFER_EDITABLE_FIELDS catalog to preserve compatibility.
#
# human_question_es: natural-language question the copilot asks when
# capturing this field conversationally (whatsapp / telegram). Ordered
# rollout — not every field has this populated yet; Fase 09 expands.
# ---------------------------------------------------------------------------

OFFER_FIELD_OVERRIDES: dict[str, Override] = {
    # ── identity ────────────────────────────────────────────────────
    "public_name": Override(
        label_es="Nombre público",
        priority=100,
        is_required_semantic=True,
        human_question_es="¿Qué nombre verá el cliente en la landing y en el agente de ventas?",
        expects="un nombre corto y memorable",
        notes="Nombre que verá el cliente en la landing y en el sales agent.",
    ),
    "internal_sku": Override(
        label_es="SKU interno",
        priority=90,
        is_required_semantic=True,
        notes="Identificador interno para analíticas y reporting.",
    ),
    "archetype": Override(
        label_es="Archetype de la oferta",
        priority=80,
        is_required_semantic=True,
        can_propose=True,
        human_question_es="¿Qué tipo de oferta es? (programa, servicio, producto, membresía, experiencia)",
        expects="uno de: PROGRAMA, SERVICIO, PRODUCTO, MEMBRESIA, EXPERIENCIA",
    ),
    "format_hint": Override(
        label_es="Formato (hint)",
        priority=50,
    ),
    "preset_id": Override(
        label_es="Preset de oferta",
        priority=40,
        can_propose=False,
        notes="Set by wizard flow, not by copilot free-form.",
    ),
    "is_lead_magnet": Override(
        label_es="Es lead magnet",
        priority=30,
        notes="Derivado de value_level cuando aplica.",
    ),
    "has_editions": Override(
        label_es="Corre en ediciones/cohortes",
        priority=20,
    ),
    # ── strategy ────────────────────────────────────────────────────
    "value_level": Override(
        label_es="Nivel de valor",
        priority=100,
        is_required_semantic=True,
        human_question_es="¿Qué nivel de valor tiene esta oferta? (lead magnet, trial, core, premium, enterprise)",
        gate="archetype",
    ),
    "delivery_model": Override(
        label_es="Modelo de entrega",
        priority=90,
    ),
    "target_avatar_match": Override(
        label_es="Avatares objetivo",
        priority=80,
        human_question_es="¿A qué avatares objetivo sirve esta oferta?",
    ),
    "anti_avatar_keywords": Override(
        label_es="Anti-avatar (palabras clave)",
        priority=70,
        notes="Palabras que descalifican a un lead. El sales-agent las usa para descartar.",
    ),
    # ── promise ─────────────────────────────────────────────────────
    "headline_promise": Override(
        label_es="Promesa principal",
        priority=100,
        is_required_semantic=True,
        human_question_es="¿Cuál es la promesa principal de esta oferta?",
        expects="una frase corta (8-15 palabras), concreta y memorable",
        notes="La gran promesa de la oferta — qué gana el cliente.",
    ),
    "primary_outcome": Override(
        label_es="Resultado principal",
        priority=95,
        is_required_semantic=True,
        human_question_es="¿Cuál es el resultado principal que obtiene el cliente?",
    ),
    "time_to_value": Override(
        label_es="Tiempo para ver valor",
        priority=90,
        human_question_es="¿En cuánto tiempo el cliente ve el primer resultado útil?",
        expects="un plazo concreto (30 días, 1 trimestre, primera semana)",
    ),
    "before_state": Override(
        label_es="Situación previa del cliente",
        priority=80,
        human_question_es="¿Cómo vive el cliente antes de comprar? Describe el dolor concreto.",
        notes="Cómo vive el cliente ANTES de la oferta. Dolor concreto y situación cotidiana específica.",
    ),
    "after_state": Override(
        label_es="Situación objetivo del cliente",
        priority=75,
        human_question_es="¿Cómo vive el cliente después de completar la oferta?",
        notes="Cómo vive el cliente DESPUÉS de completar la oferta. Evidencia concreta, no abstracta.",
    ),
    "why_now": Override(
        label_es="Por qué ahora",
        priority=70,
        human_question_es="¿Por qué tiene costo concreto postergar esta decisión?",
        notes="Razón por la que postergar tiene costo concreto. Evita escasez falsa.",
    ),
    "measurable_outcomes": Override(
        label_es="Resultados medibles",
        priority=65,
        human_question_es="¿Qué resultados medibles concretos logra el cliente?",
        notes="Lista de resultados medibles concretos, uno por ítem. Idealmente con números.",
    ),
    "requires_application": Override(
        label_es="Requiere aplicación",
        priority=40,
    ),
    "min_financial_capacity": Override(
        label_es="Capacidad financiera mínima",
        priority=35,
    ),
    "prerequisites": Override(
        label_es="Prerequisitos",
        priority=30,
    ),
    # ── psychology ──────────────────────────────────────────────────
    "marketing_pain_points": Override(
        label_es="Pain points de marketing",
        priority=100,
        human_question_es="¿Qué dolores concretos siente el avatar de esta oferta?",
        notes="Dolores específicos y medibles. El agente los cita textualmente.",
    ),
    "marketing_desires": Override(
        label_es="Deseos de marketing",
        priority=95,
        human_question_es="¿Qué desea concretamente el avatar?",
        notes="Deseos concretos del avatar. Con números cuando aplique.",
    ),
    "objections": Override(
        label_es="Objeciones",
        priority=90,
        human_question_es="¿Qué objeciones tiene el avatar antes de comprar?",
        notes="Objeciones anticipadas estructuradas con type/trigger_phrases/strategy/rebuttal.",
    ),
    "cultural_trust_barriers": Override(
        label_es="Barreras culturales de confianza",
        priority=80,
        notes="Barreras culturales Latam que no son objeciones clásicas.",
    ),
    "emotional_triggers": Override(
        label_es="Disparadores emocionales",
        priority=75,
        notes="Miedos, deseos y aspiraciones que mueven la decisión.",
    ),
    "status_drivers": Override(
        label_es="Motores de estatus",
        priority=70,
        notes="Qué cambia en la percepción social del cliente cuando tiene éxito.",
    ),
    "regret_scenarios": Override(
        label_es="Escenarios de arrepentimiento",
        priority=65,
        notes="Situaciones futuras donde el lead se va a arrepentir de no haber comprado.",
    ),
    # ── instructors ─────────────────────────────────────────────────
    "instructors": Override(
        label_es="Instructores",
        priority=100,
        human_question_es="¿Quiénes son los instructores o facilitadores?",
    ),
    "authority_positioning_for_sales": Override(
        label_es="Posicionamiento de autoridad",
        priority=90,
        notes="Narrativa + credenciales para sales-agent cuando el lead pregunta por el instructor.",
    ),
    "authority_notes": Override(
        label_es="Notas de autoridad",
        priority=80,
        notes="Credenciales puntuales de la oferta (speakers invitados, coaches).",
    ),
    # ── value_stack ─────────────────────────────────────────────────
    "deliverables": Override(
        label_es="Entregables",
        priority=100,
        is_required_semantic=True,
        human_question_es="¿Qué entregables incluye la oferta?",
    ),
    "includes_offers": Override(
        label_es="Ofertas incluidas",
        priority=80,
    ),
    "total_perceived_value_anchor": Override(
        label_es="Valor total percibido (ancla USD)",
        priority=70,
        notes="USD anchor surfacing on landing + sales-agent closing scripts.",
    ),
    "stack_positioning_statement": Override(
        label_es="Posicionamiento del stack",
        priority=60,
        notes="2-3 líneas que resumen el trade-off valor↔precio.",
    ),
    # ── pricing ─────────────────────────────────────────────────────
    "pricing_options": Override(
        label_es="Opciones de precio",
        priority=100,
        is_required_semantic=True,
        notes="List of PricingStructure (plan_type, total_amount, installments, ...).",
    ),
    "price_pay_in_full": Override(
        label_es="Precio pago único",
        priority=90,
        notes="USD equivalent for cross-currency benchmarks.",
    ),
    "currency": Override(
        label_es="Moneda",
        priority=80,
        notes="ISO 4217. Falls back to TenantLocale.currency when null.",
    ),
    "tax_included": Override(
        label_es="Impuestos incluidos",
        priority=70,
        human_question_es="¿El precio incluye IVA/IGV/ICMS?",
        expects="sí, no, o no aplica",
        notes="IVA/IGV/ICMS inclusion flag. Avoids Latam checkout disputes.",
    ),
    "installments_available": Override(
        label_es="Cuotas disponibles",
        priority=60,
        human_question_es="¿Qué cuotas sin interés acepta?",
        expects="números separados por coma (por ejemplo: 3, 6, 12)",
        notes="Free-text installment counts. Decisive for Latam tickets >USD 100.",
    ),
    "accepted_payment_providers": Override(
        label_es="Providers de pago aceptados",
        priority=50,
        can_propose=False,
        notes=(
            "UI-configured via Conexiones; not LLM-extracted (ADR-009). Providers: stripe/mercadopago/culqi/manual."
        ),
    ),
    # ── closing ─────────────────────────────────────────────────────
    "guarantee_type": Override(
        label_es="Tipo de garantía",
        priority=100,
        is_required_semantic=True,
    ),
    "guarantee_terms": Override(
        label_es="Términos de la garantía",
        priority=95,
        is_required_semantic=True,
        notes="Copia textual para landing + checkout + email. Tono confiado, sin letra chica.",
    ),
    "support_duration_days": Override(
        label_es="Duración del soporte (días)",
        priority=90,
        notes="Cuántos días el cliente tiene acceso al soporte post-compra.",
    ),
    "refund_process_description": Override(
        label_es="Proceso de devolución",
        priority=85,
        notes="Cómo se devuelve el dinero, desglosado por método de pago. Combate la desconfianza Latam.",
    ),
    "urgency_drivers": Override(
        label_es="Razones de urgencia honestas",
        priority=80,
        notes="Razones HONESTAS para comprar ahora. Urgencia falsa pierde confianza.",
    ),
    "scarcity_reason_honest": Override(
        label_es="Motivo de escasez real",
        priority=75,
        notes="Razón honesta de los cupos limitados — logística real, tiempo del experto.",
    ),
    "bonus_if_act_now": Override(
        label_es="Bonus por decidir ahora",
        priority=70,
        notes="Bonus condicional a actuar en una ventana definida (48h, 7 días).",
    ),
    "final_push_copy": Override(
        label_es="Frase de cierre",
        priority=65,
        notes="Frase de cierre emocional para cuando el lead está a un paso.",
    ),
    "checkout_page_url": Override(
        label_es="URL de checkout",
        priority=60,
    ),
    "calendar_type_id": Override(
        label_es="Calendario de citas",
        priority=55,
    ),
    "onboarding_action": Override(
        label_es="Acción de onboarding",
        priority=50,
    ),
    "onboarding_url": Override(
        label_es="URL de onboarding",
        priority=45,
    ),
    "downsell_offer_id": Override(
        label_es="Oferta downsell",
        priority=30,
    ),
    "upsell_offer_id": Override(
        label_es="Oferta upsell",
        priority=25,
    ),
    "vsl_link": Override(
        label_es="VSL link",
        priority=20,
    ),
    "access_duration": Override(
        label_es="Duración del acceso (enum)",
        priority=15,
    ),
    "access_duration_text": Override(
        label_es="Duración del acceso",
        priority=10,
    ),
    # ── Program details (selected high-signal overrides) ────────────
    "specific_details.weekly_time_commitment_hours": Override(
        human_question_es="¿Cuántas horas semanales requiere el programa?",
        expects="un número de horas por semana",
    ),
    "specific_details.prerequisites_text": Override(
        human_question_es="¿Qué prerequisitos tiene el programa?",
    ),
    # ── Subscription details ────────────────────────────────────────
    "specific_details.billing_frequency": Override(
        human_question_es="¿Con qué frecuencia se factura la membresía? (mensual, trimestral, anual)",
    ),
    # ── Product details ─────────────────────────────────────────────
    "specific_details.return_policy_days": Override(
        human_question_es="¿Cuántos días de devolución ofrece el producto?",
    ),
    # ── Platform details ────────────────────────────────────────────
    "platform_details.api_available": Override(
        human_question_es="¿Tiene API pública?",
    ),
    "platform_details.uptime_guarantee": Override(
        human_question_es="¿Qué SLA de uptime ofrece?",
    ),
}


# ---------------------------------------------------------------------------
# Build OFFER_FIELD_CONTRACTS + register with shared platform
# ---------------------------------------------------------------------------

OFFER_FIELD_CONTRACTS: tuple[FieldContract, ...] = derive_contracts_from_pydantic(
    model=Offer,
    owner_module="offer",
    section_map=OFFER_SECTION_MAP,
    overrides=OFFER_FIELD_OVERRIDES,
    ignore_paths=OFFER_IGNORE_PATHS,
    polymorphic_prefix_map=_build_polymorphic_prefix_map(),
    composable_fields=("platform_details",),
)

register_module_contracts("offer", OFFER_FIELD_CONTRACTS)


# ---------------------------------------------------------------------------
# Backward-compat aliases
#
# Existing consumers (endpoint, tests, legacy code) expect these names.
# Keep them as light aliases / projections so refactor is transparent.
# Can be removed in a later cleanup once all consumers migrate to the
# shared accessors directly.
# ---------------------------------------------------------------------------

FIELD_CONTRACT_REGISTRY: tuple[FieldContract, ...] = OFFER_FIELD_CONTRACTS
"""Legacy alias for the full offer registry."""

PRICING_FIELD_CONTRACTS: tuple[FieldContract, ...] = tuple(_shared_fields_by_section("offer", "pricing"))
"""Legacy alias used by tests. Narrowed to ACTIVE status."""


def contracts_by_section(section: str) -> tuple[FieldContract, ...]:
    """Return ACTIVE offer contracts for a given section slug.

    Legacy helper preserved for backward compatibility.
    """
    return _shared_fields_by_section("offer", section, status=FieldStatus.ACTIVE)


FIELD_CONTRACT_VERSION = "2026-04-24-fase-04-platform-derived"
"""Bumped when overrides or section map change materially."""

FIELD_CONTRACT_SNAPSHOT = FieldContractRegistrySnapshot(
    version=FIELD_CONTRACT_VERSION,
    module="offer",
    contracts=OFFER_FIELD_CONTRACTS,
)


__all__ = [
    "FIELD_CONTRACT_REGISTRY",
    "FIELD_CONTRACT_SNAPSHOT",
    "FIELD_CONTRACT_VERSION",
    "OFFER_FIELD_CONTRACTS",
    "OFFER_FIELD_OVERRIDES",
    "OFFER_IGNORE_PATHS",
    "OFFER_SECTION_MAP",
    "PRICING_FIELD_CONTRACTS",
    "contracts_by_section",
]
