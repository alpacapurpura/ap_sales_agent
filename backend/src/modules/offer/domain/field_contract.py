"""FieldContract — structural SSoT for Offer schema fields.

Fase 01 pilot (pricing LATAM). FieldContract separates the **structural
contract** (path, type, ownership, requiredness, archetype filter) from
the **UX presentation layer** (label, hint, placeholder, copy) that
schemas in ``frontend/src/features/offer-studio/schemas/`` describe.

Motivation: see ``docs/refactors/field-contract-ssot/DECISIONS.md`` ADR-001.

Pilot scope: only the pricing section is modeled here. Phases 02→04 port
the remaining sections and eventually derive ``OFFER_FIELDS_BY_FE_SECTION``
from this registry.

Consumers:
- ``GET /api/v1/offer/field-contract`` serialises this registry.
- Frontend typechecks schema ``path`` literals against the generated
  ``OfferFieldPath`` TS union (codegen from the registry + Offer
  introspection).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.modules.offer.domain.enums import FieldOwner, OfferArchetype


@dataclass(frozen=True, slots=True)
class FieldContract:
    """Structural contract for a single offer-studio field.

    Immutable (frozen) + slotted so the registry can be treated as a
    compile-time constant. Mirrors the ``field-contract-ssot`` refactor
    goal: every FE schema path MUST resolve to a contract here by Fase 04.

    Attributes:
        path: Dotted path into the Offer aggregate (``headline_promise``,
            ``pricing_options``, ``specific_details.cohort_limit``, etc).
            Matches ``backend/tests/architecture/fixtures/offer_field_paths.json``.
        type: Persistence type hint ("bool", "text", "number", "list",
            "object", "enum"). Used by codegen + completion rules.
        owner: Which aggregate persists the field. ``OFFER`` for most,
            ``EDITION`` for edition-scoped ones (pricing_tiers).
        section: Section slug under ``OFFER_SECTIONS`` (e.g. ``pricing``,
            ``closing``). Drives FE grouping.
        required: Whether the field must be filled before the section is
            considered complete.
        archetype_filter: Subset of archetypes for which the field is
            visible. ``None`` = universal.
    """

    path: str
    type: str
    owner: FieldOwner
    section: str
    required: bool = False
    archetype_filter: tuple[OfferArchetype, ...] | None = None
    # Optional human-readable notes for BE consumers (sales-agent, landing).
    # NOT UX copy — that lives in FE schemas. Here for structural hints.
    notes: str | None = None


# ---------------------------------------------------------------------------
# Pricing section — 6 fields (3 legacy + 3 new LATAM, Fase 01 pilot)
# ---------------------------------------------------------------------------

PRICING_SECTION = "pricing"

PRICING_FIELD_CONTRACTS: tuple[FieldContract, ...] = (
    FieldContract(
        path="pricing_options",
        type="list",
        owner=FieldOwner.OFFER,
        section=PRICING_SECTION,
        required=True,
        notes="List of PricingStructure (plan_type, total_amount, installments, ...).",
    ),
    FieldContract(
        path="currency",
        type="text",
        owner=FieldOwner.OFFER,
        section=PRICING_SECTION,
        required=False,
        notes="ISO 4217. Falls back to TenantLocale.currency when null.",
    ),
    FieldContract(
        path="price_pay_in_full",
        type="number",
        owner=FieldOwner.OFFER,
        section=PRICING_SECTION,
        required=False,
        notes="USD equivalent for cross-currency benchmarks.",
    ),
    FieldContract(
        path="tax_included",
        type="bool",
        owner=FieldOwner.OFFER,
        section=PRICING_SECTION,
        required=False,
        notes="IVA/IGV/ICMS inclusion flag. Avoids Latam checkout disputes.",
    ),
    FieldContract(
        path="installments_available",
        type="text",
        owner=FieldOwner.OFFER,
        section=PRICING_SECTION,
        required=False,
        notes="Free-text installment counts (e.g. '3, 6, 12').",
    ),
    FieldContract(
        path="accepted_payment_providers",
        type="list",
        owner=FieldOwner.OFFER,
        section=PRICING_SECTION,
        required=False,
        notes=(
            "list[str] — IDs from sales_agent.PaymentProvider. UI-configured"
            " via Conexiones; not LLM-extracted (ADR-009)."
        ),
    ),
)


# ---------------------------------------------------------------------------
# Instructors / authority section — 2 fields (Fase 02 · Block A)
# ---------------------------------------------------------------------------

INSTRUCTORS_SECTION = "instructors"

INSTRUCTORS_FIELD_CONTRACTS: tuple[FieldContract, ...] = (
    FieldContract(
        path="authority_positioning_for_sales",
        type="text",
        owner=FieldOwner.OFFER,
        section=INSTRUCTORS_SECTION,
        required=False,
        notes=(
            "Narrativa + credenciales para sales-agent cuando el lead"
            " pregunta por el instructor. Reemplaza listados planos."
        ),
    ),
    FieldContract(
        path="authority_notes",
        type="text",
        owner=FieldOwner.OFFER,
        section=INSTRUCTORS_SECTION,
        required=False,
        notes=(
            "Credenciales puntuales de la oferta (speakers invitados,"
            " coaches). No mutan el perfil maestro del instructor."
        ),
    ),
)


# ---------------------------------------------------------------------------
# Value-stack section — anchor + positioning statement (Fase 02 · Block B)
# ---------------------------------------------------------------------------

VALUE_STACK_SECTION = "value_stack"

VALUE_STACK_FIELD_CONTRACTS: tuple[FieldContract, ...] = (
    FieldContract(
        path="total_perceived_value_anchor",
        type="number",
        owner=FieldOwner.OFFER,
        section=VALUE_STACK_SECTION,
        required=False,
        notes=(
            "USD anchor for the stack. Surfaced on landing and sales-agent"
            " closing scripts as 'Valor total USD X · Tu inversión USD Y'."
        ),
    ),
    FieldContract(
        path="stack_positioning_statement",
        type="text",
        owner=FieldOwner.OFFER,
        section=VALUE_STACK_SECTION,
        required=False,
        notes=(
            "2-3 line statement framing the value/price trade-off. Reused by landing + sales-agent; additive render."
        ),
    ),
)


# ---------------------------------------------------------------------------
# Program details section — narrative commitments (Fase 02 · Block C)
# ---------------------------------------------------------------------------

PROGRAM_DETAILS_SECTION = "program_details"

PROGRAM_DETAILS_FIELD_CONTRACTS: tuple[FieldContract, ...] = (
    FieldContract(
        path="specific_details.weekly_time_commitment_hours",
        type="number",
        owner=FieldOwner.OFFER,
        section=PROGRAM_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.PROGRAMA,),
        notes=(
            "Expected weekly hours the student must dedicate (videos +"
            " practice + live + community). Most-asked question pre-buy."
        ),
    ),
    FieldContract(
        path="specific_details.prerequisites_text",
        type="text",
        owner=FieldOwner.OFFER,
        section=PROGRAM_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.PROGRAMA,),
        notes=(
            "Narrative prerequisites replacing the legacy categorical"
            " enum. Empty → no gates. Filters expectation, not access."
        ),
    ),
)


# ---------------------------------------------------------------------------
# Subscription details section — renames + Latam compliance (Fase 02 · Block D)
# ---------------------------------------------------------------------------

SUBSCRIPTION_DETAILS_SECTION = "subscription_details"

SUBSCRIPTION_DETAILS_FIELD_CONTRACTS: tuple[FieldContract, ...] = (
    FieldContract(
        path="specific_details.billing_frequency",
        type="enum",
        owner=FieldOwner.OFFER,
        section=SUBSCRIPTION_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.MEMBRESIA,),
        notes="Renamed from billing_cycle. Monthly/quarterly/annual/one_off.",
    ),
    FieldContract(
        path="specific_details.content_update_frequency",
        type="enum",
        owner=FieldOwner.OFFER,
        section=SUBSCRIPTION_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.MEMBRESIA,),
        notes="Renamed from content_update_freq.",
    ),
    FieldContract(
        path="specific_details.auto_renewal_with_notice_days",
        type="number",
        owner=FieldOwner.OFFER,
        section=SUBSCRIPTION_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.MEMBRESIA,),
        notes="Latam legal: notice days before debit on auto-renewal. 3-7 standard.",
    ),
    FieldContract(
        path="specific_details.cancellation_anticipation_days",
        type="number",
        owner=FieldOwner.OFFER,
        section=SUBSCRIPTION_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.MEMBRESIA,),
        notes="Days of anticipation required to cancel before next cycle.",
    ),
    FieldContract(
        path="specific_details.grace_period_days_on_failed_payment",
        type="number",
        owner=FieldOwner.OFFER,
        section=SUBSCRIPTION_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.MEMBRESIA,),
        notes="Grace window to retry failed payments. Recovers 30-50% involuntary churn.",
    ),
    FieldContract(
        path="specific_details.member_benefits",
        type="text",
        owner=FieldOwner.OFFER,
        section=SUBSCRIPTION_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.MEMBRESIA,),
        notes="Narrative one-per-line benefits the member receives.",
    ),
    FieldContract(
        path="specific_details.primary_communication_channel",
        type="enum",
        owner=FieldOwner.OFFER,
        section=SUBSCRIPTION_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.MEMBRESIA,),
        notes="Ongoing communication channel (whatsapp_business/email/slack_shared/telegram/platform_internal).",
    ),
)


# ---------------------------------------------------------------------------
# Service details section — scope + expectation (Fase 02 · Block E)
# ---------------------------------------------------------------------------

SERVICE_DETAILS_SECTION = "service_details"

SERVICE_DETAILS_FIELD_CONTRACTS: tuple[FieldContract, ...] = (
    FieldContract(
        path="specific_details.response_time_hours",
        type="number",
        owner=FieldOwner.OFFER,
        section=SERVICE_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.SERVICIO,),
        notes="Agent-facing SLA: horas hábiles para responder al cliente.",
    ),
    FieldContract(
        path="specific_details.onboarding_flow",
        type="text",
        owner=FieldOwner.OFFER,
        section=SERVICE_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.SERVICIO,),
        notes="Narrativa de qué recibe el cliente en las primeras 24-48h.",
    ),
    FieldContract(
        path="specific_details.scope_excluded",
        type="text",
        owner=FieldOwner.OFFER,
        section=SERVICE_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.SERVICIO,),
        notes="Scope-out explícito — evita 80% disputas post-venta Latam.",
    ),
)


# ---------------------------------------------------------------------------
# Product details section — preview + physical logistics (Fase 02 · Block F)
# ---------------------------------------------------------------------------

PRODUCT_DETAILS_SECTION = "product_details"

PRODUCT_DETAILS_FIELD_CONTRACTS: tuple[FieldContract, ...] = (
    FieldContract(
        path="specific_details.sample_preview_url",
        type="text",
        owner=FieldOwner.OFFER,
        section=PRODUCT_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.PRODUCTO,),
        notes="URL de sample gratuito — convierte 30-50% más.",
    ),
    FieldContract(
        path="specific_details.packaging_description",
        type="text",
        owner=FieldOwner.OFFER,
        section=PRODUCT_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.PRODUCTO,),
        notes="Experiencia unboxing (productos físicos). Compartible.",
    ),
    FieldContract(
        path="specific_details.return_policy_days",
        type="number",
        owner=FieldOwner.OFFER,
        section=PRODUCT_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.PRODUCTO,),
        notes="Días de devolución. Mínimo legal AR/PE 7, CO 10, MX 30.",
    ),
    FieldContract(
        path="specific_details.shipping_carriers_accepted",
        type="text",
        owner=FieldOwner.OFFER,
        section=PRODUCT_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.PRODUCTO,),
        notes="Carriers Latam (Mercado Envíos, Andreani, OCA, Servientrega, etc).",
    ),
    FieldContract(
        path="specific_details.shipping_estimate_by_region",
        type="text",
        owner=FieldOwner.OFFER,
        section=PRODUCT_DETAILS_SECTION,
        required=False,
        archetype_filter=(OfferArchetype.PRODUCTO,),
        notes="Tiempos por región (Capital/Interior/Internacional).",
    ),
)


# ---------------------------------------------------------------------------
# Platform details section — composable SaaS (Fase 02 · Block G, ADR-010)
# ---------------------------------------------------------------------------

PLATFORM_DETAILS_SECTION = "platform_details"

PLATFORM_DETAILS_FIELD_CONTRACTS: tuple[FieldContract, ...] = (
    FieldContract(
        path="platform_details.platform_features",
        type="list",
        owner=FieldOwner.OFFER,
        section=PLATFORM_DETAILS_SECTION,
        required=False,
        notes="List[PlatformFeature]: core features con plan matrix.",
    ),
    FieldContract(
        path="platform_details.platform_integrations",
        type="list",
        owner=FieldOwner.OFFER,
        section=PLATFORM_DETAILS_SECTION,
        required=False,
        notes="List[PlatformIntegration]: integrations externas (Mercado Pago, WhatsApp, etc.).",
    ),
    FieldContract(
        path="platform_details.security_compliance",
        type="text",
        owner=FieldOwner.OFFER,
        section=PLATFORM_DETAILS_SECTION,
        required=False,
        notes="Certificaciones SOC2/ISO + frameworks Latam (LGPD/Habeas Data/PDPL).",
    ),
    FieldContract(
        path="platform_details.data_residency",
        type="text",
        owner=FieldOwner.OFFER,
        section=PLATFORM_DETAILS_SECTION,
        required=False,
        notes="Región en que se hostean los datos (AWS sa-east-1, etc.).",
    ),
    FieldContract(
        path="platform_details.uptime_guarantee",
        type="text",
        owner=FieldOwner.OFFER,
        section=PLATFORM_DETAILS_SECTION,
        required=False,
        notes="SLA de uptime (99.9%, 99.95%, etc.).",
    ),
    FieldContract(
        path="platform_details.status_page_url",
        type="text",
        owner=FieldOwner.OFFER,
        section=PLATFORM_DETAILS_SECTION,
        required=False,
        notes="URL pública del status page.",
    ),
    FieldContract(
        path="platform_details.support_channels",
        type="text",
        owner=FieldOwner.OFFER,
        section=PLATFORM_DETAILS_SECTION,
        required=False,
        notes="Canales + horarios + SLA de respuesta.",
    ),
    FieldContract(
        path="platform_details.api_available",
        type="bool",
        owner=FieldOwner.OFFER,
        section=PLATFORM_DETAILS_SECTION,
        required=False,
        notes="True si hay API pública.",
    ),
    FieldContract(
        path="platform_details.api_docs_url",
        type="text",
        owner=FieldOwner.OFFER,
        section=PLATFORM_DETAILS_SECTION,
        required=False,
        notes="URL de docs de API (ReadMe, Mintlify, GitBook).",
    ),
    FieldContract(
        path="platform_details.migration_tools",
        type="text",
        owner=FieldOwner.OFFER,
        section=PLATFORM_DETAILS_SECTION,
        required=False,
        notes="Herramientas para migrar desde competidores.",
    ),
    FieldContract(
        path="platform_details.public_roadmap_url",
        type="text",
        owner=FieldOwner.OFFER,
        section=PLATFORM_DETAILS_SECTION,
        required=False,
        notes="Roadmap público (Trello/Productboard/Canny).",
    ),
    FieldContract(
        path="platform_details.changelog_url",
        type="text",
        owner=FieldOwner.OFFER,
        section=PLATFORM_DETAILS_SECTION,
        required=False,
        notes="Página pública de releases.",
    ),
    FieldContract(
        path="platform_details.ai_features_disclosure",
        type="text",
        owner=FieldOwner.OFFER,
        section=PLATFORM_DETAILS_SECTION,
        required=False,
        notes="Transparencia de uso de IA (exigencia regulatoria Latam creciente).",
    ),
    FieldContract(
        path="platform_details.data_export_capability",
        type="text",
        owner=FieldOwner.OFFER,
        section=PLATFORM_DETAILS_SECTION,
        required=False,
        notes="Derecho de portabilidad (GDPR/LGPD/Habeas Data/PDPL).",
    ),
)


# ---------------------------------------------------------------------------
# Registry (grows per phase — F01 pricing · F02 A authority B value-stack
# C program D subscription E service F product G platform)
# ---------------------------------------------------------------------------

_PHASE_01_CONTRACTS: tuple[FieldContract, ...] = PRICING_FIELD_CONTRACTS
_PHASE_02_CONTRACTS: tuple[FieldContract, ...] = (
    INSTRUCTORS_FIELD_CONTRACTS
    + VALUE_STACK_FIELD_CONTRACTS
    + PROGRAM_DETAILS_FIELD_CONTRACTS
    + SUBSCRIPTION_DETAILS_FIELD_CONTRACTS
    + SERVICE_DETAILS_FIELD_CONTRACTS
    + PRODUCT_DETAILS_FIELD_CONTRACTS
    + PLATFORM_DETAILS_FIELD_CONTRACTS
)

FIELD_CONTRACT_REGISTRY: tuple[FieldContract, ...] = _PHASE_01_CONTRACTS + _PHASE_02_CONTRACTS


def contracts_by_section(section: str) -> tuple[FieldContract, ...]:
    """Return all contracts for a given section slug."""
    return tuple(fc for fc in FIELD_CONTRACT_REGISTRY if fc.section == section)


@dataclass(frozen=True, slots=True)
class FieldContractRegistrySnapshot:
    """Versioned snapshot returned by ``/api/v1/offer/field-contract``.

    The ``version`` string is bumped every time the registry changes —
    clients cache by it, so a deploy invalidates their local cache.
    """

    version: str
    contracts: tuple[FieldContract, ...] = field(default_factory=tuple)


# Bump when the registry changes materially.
FIELD_CONTRACT_VERSION = "2026-04-24-fase-02-block-g-platform-composable"

FIELD_CONTRACT_SNAPSHOT = FieldContractRegistrySnapshot(
    version=FIELD_CONTRACT_VERSION,
    contracts=FIELD_CONTRACT_REGISTRY,
)
