"""Archetype Capabilities Catalog — single source of truth for offer archetypes.

This module declares what each ``OfferArchetype`` supports at the domain level:
edition capability, required fields for public publishing, default delivery
model, and user-facing labels.

Any scattered logic about archetypes (domain validators, interview configs,
frontend helpers) MUST delegate to this catalog via ``get_capabilities()``
instead of duplicating knowledge. The architecture test
``tests/architecture/test_archetype_catalog.py`` enforces that every
``OfferArchetype`` enum value is represented here.

Why a frozen ``dataclass`` constant and not a DB table:
- capabilities are invariants of the domain, not runtime config
- changing capabilities implies code changes (new validators, new UI)
- arch tests guarantee drift-free refactoring
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.modules.offer.domain.enums import (
    FulfillmentType,
    OfferArchetype,
    OfferDeliveryModel,
    VariantStructure,
)
from src.modules.offer.domain.section_catalog import SectionKey


@dataclass(frozen=True, slots=True)
class ArchetypeCapabilities:
    """Capabilities and defaults for a single ``OfferArchetype``.

    The record is frozen to prevent mutation at runtime. All fields participate
    in the architecture test surface.
    """

    archetype: OfferArchetype

    # Variant / edition capability.
    # ``supports_editions`` is the canonical predicate: True iff the archetype
    # admits a ``LaunchEdition`` (variant instance). The noun labels drive UX
    # copy via ``VariantStructureMetadata.noun_es`` — kept here as overrides
    # when the archetype's canonical noun differs from the default variant
    # structure's noun (e.g. COACH_MEMBRESIA still says "plan" regardless of
    # which structure is chosen for a specific tenant).
    supports_editions: bool
    edition_noun_es: str
    edition_noun_plural_es: str

    # Publishing constraints — enforced when an edition transitions to public
    requires_start_date_on_publish: bool
    requires_end_date_on_publish: bool
    requires_location_on_publish: bool
    supports_capacity: bool
    supports_waitlist: bool

    # Defaults propagated to the Offer entity at creation
    default_delivery: OfferDeliveryModel
    default_fulfillment: FulfillmentType

    # User-facing labels (Spanish — matches UI language)
    label_es: str
    subtitle_es: str
    icon_name: str  # lucide-react icon name for the frontend
    # Canonical examples list surfaced in the Offer Studio wizard archetype
    # picker + the dashboard cards. Frontend previously hardcoded these in
    # ``archetype-metadata.ts`` — now the backend is the single source.
    examples_es: tuple[str, ...] = field(default_factory=tuple)

    # Ordered tuple of editor sections this archetype surfaces. Frontend
    # renders the section rail in this order. Backend SSoT — frontend
    # duplicates are rejected by ``test-no-section-catalog-duplicates``.
    # Scope invariants enforced by ``test_archetype_sections_alignment``:
    # edition-less archetypes must not list EDITION_LEVEL sections, and
    # edition-supporting archetypes must list at least one non-OFFER_LEVEL
    # section. Defaults to empty tuple so older records (if any) still
    # construct; per-archetype records declare this explicitly.
    sections: tuple[SectionKey, ...] = field(default_factory=tuple)

    # Wizard copy for the "will this offer have editions?" question.
    # Present iff supports_editions is True — frontend renders the wizard step
    # only when all four fields are set.
    editions_wizard_title_es: str | None = None
    editions_wizard_description_es: str | None = None
    editions_wizard_yes_label_es: str | None = None
    editions_wizard_no_label_es: str | None = None

    # Default ``VariantStructure`` assigned to the placeholder edition spawned
    # at offer creation. ``None`` iff the archetype does not support editions.
    # Promoted from migration 049's hard-coded SQL mapping into the catalog so
    # the archetype-↔-structure relation has a single source of truth. The
    # arch test ``test_archetype_default_variant_structure_alignment`` blocks
    # any drift between ``supports_editions`` and this field.
    default_variant_structure: VariantStructure | None = None

    # Ordered tuple of ``VariantStructure`` values the archetype accepts. The
    # wizard renders a "¿Cómo varía tu oferta?" step ONLY when this tuple
    # holds more than one entry — presets can fix the structure up front via
    # ``OfferTypePreset.default_variant_structure`` to skip the step. The
    # default MUST be a member of this tuple (enforced by
    # ``test_archetype_default_in_supported_variant_structures``).
    supported_variant_structures: tuple[VariantStructure, ...] = field(default_factory=tuple)

    # True when the UX may collapse a single-variant offer into a direct
    # editor without rendering the collection landing page (TIER membership
    # with one plan, PRODUCTO with one SKU). Archetypes whose variant is
    # intrinsically plural (PROGRAMA cohortes) should keep this False — the
    # rail is part of the mental model even when only one cohort exists yet.
    allow_single_variant: bool = False


ARCHETYPE_CATALOG: dict[OfferArchetype, ArchetypeCapabilities] = {
    OfferArchetype.EXPERIENCIA: ArchetypeCapabilities(
        archetype=OfferArchetype.EXPERIENCIA,
        supports_editions=True,
        edition_noun_es="salida",
        edition_noun_plural_es="salidas",
        requires_start_date_on_publish=True,
        requires_end_date_on_publish=False,
        requires_location_on_publish=True,
        supports_capacity=True,
        supports_waitlist=True,
        default_delivery=OfferDeliveryModel.DWY,
        default_fulfillment=FulfillmentType.MANUAL_PROVISIONING,
        default_variant_structure=VariantStructure.TEMPORAL_SINGLE_DATE,
        supported_variant_structures=(
            VariantStructure.TEMPORAL_SINGLE_DATE,
            VariantStructure.MODALITY,
            VariantStructure.LANGUAGE,
            VariantStructure.REGIONAL,
        ),
        allow_single_variant=True,
        label_es="Experiencia / Evento",
        subtitle_es="Un momento o evento único",
        icon_name="Tent",
        examples_es=(
            "Webinar",
            "Retiro",
            "Taller",
            "Conferencia",
            "Capacitación presencial",
        ),
        editions_wizard_title_es="¿Tendrá varias salidas en fechas distintas?",
        editions_wizard_description_es=(
            "Si vas a repetir esta experiencia en distintas fechas (ej: cada trimestre), elige Sí."
        ),
        editions_wizard_yes_label_es="Sí, con múltiples salidas programadas",
        editions_wizard_no_label_es="No, es una corrida única",
        sections=(
            SectionKey.IDENTITY,
            SectionKey.STRATEGY,
            SectionKey.PSYCHOLOGY,
            SectionKey.PROMISE,
            SectionKey.EVENT_DETAILS,
            SectionKey.LOCATION,
            SectionKey.INSTRUCTORS,
            SectionKey.VALUE_STACK,
            SectionKey.TESTIMONIALS,
            SectionKey.PORTFOLIO,
            SectionKey.FAQ,
            SectionKey.GALLERY,
            SectionKey.RESOURCES,
            SectionKey.PRICING,
            SectionKey.CLOSING,
            SectionKey.KNOWLEDGE,
        ),
    ),
    OfferArchetype.PROGRAMA: ArchetypeCapabilities(
        archetype=OfferArchetype.PROGRAMA,
        supports_editions=True,
        edition_noun_es="cohorte",
        edition_noun_plural_es="cohortes",
        requires_start_date_on_publish=True,
        requires_end_date_on_publish=True,
        requires_location_on_publish=False,
        supports_capacity=True,
        supports_waitlist=True,
        default_delivery=OfferDeliveryModel.DWY,
        default_fulfillment=FulfillmentType.LMS_ACCESS,
        default_variant_structure=VariantStructure.TEMPORAL_COHORT,
        supported_variant_structures=(
            VariantStructure.TEMPORAL_COHORT,
            VariantStructure.MODALITY,
            VariantStructure.LANGUAGE,
            VariantStructure.REGIONAL,
        ),
        allow_single_variant=False,
        label_es="Programa",
        subtitle_es="Un proceso con inicio, pasos y resultado",
        icon_name="Map",
        examples_es=(
            "Mentoría grupal",
            "Plan personalizado",
            "Bootcamp",
            "Cohorte",
        ),
        editions_wizard_title_es="¿Se dictará en cohortes?",
        editions_wizard_description_es=(
            "Las cohortes son grupos de alumnos que empiezan y terminan juntos en fechas fijas."
        ),
        editions_wizard_yes_label_es="Sí, en cohortes con fechas fijas",
        editions_wizard_no_label_es="No, es evergreen (cada alumno entra cuando quiere)",
        sections=(
            SectionKey.IDENTITY,
            SectionKey.STRATEGY,
            SectionKey.PSYCHOLOGY,
            SectionKey.PROMISE,
            SectionKey.PROGRAM_DETAILS,
            SectionKey.INSTRUCTORS,
            SectionKey.VALUE_STACK,
            SectionKey.TESTIMONIALS,
            SectionKey.PORTFOLIO,
            SectionKey.FAQ,
            SectionKey.GALLERY,
            SectionKey.RESOURCES,
            SectionKey.PRICING,
            SectionKey.CLOSING,
            SectionKey.KNOWLEDGE,
        ),
    ),
    OfferArchetype.SERVICIO: ArchetypeCapabilities(
        archetype=OfferArchetype.SERVICIO,
        supports_editions=True,
        edition_noun_es="convocatoria",
        edition_noun_plural_es="convocatorias",
        requires_start_date_on_publish=False,
        requires_end_date_on_publish=False,
        requires_location_on_publish=False,
        supports_capacity=True,
        supports_waitlist=False,
        default_delivery=OfferDeliveryModel.DFY,
        default_fulfillment=FulfillmentType.MANUAL_PROVISIONING,
        default_variant_structure=VariantStructure.RECURRING_INTAKE,
        supported_variant_structures=(
            VariantStructure.RECURRING_INTAKE,
            VariantStructure.TIER,
            VariantStructure.MODALITY,
            VariantStructure.LANGUAGE,
            VariantStructure.REGIONAL,
        ),
        allow_single_variant=True,
        label_es="Servicio",
        subtitle_es="Trabajo que hago para o con alguien",
        icon_name="Wrench",
        examples_es=(
            "Consultoría",
            "Auditoría",
            "Diseño web",
            "VIP Day",
            "Retainer",
        ),
        editions_wizard_title_es="¿Se ofrecerá en convocatorias?",
        editions_wizard_description_es=(
            "Las convocatorias agrupan clientes que empiezan al mismo tiempo en fechas fijas."
        ),
        editions_wizard_yes_label_es="Sí, con convocatorias agrupadas",
        editions_wizard_no_label_es="No, cada cliente agenda su propia fecha",
        sections=(
            SectionKey.IDENTITY,
            SectionKey.STRATEGY,
            SectionKey.PSYCHOLOGY,
            SectionKey.PROMISE,
            SectionKey.SERVICE_DETAILS,
            SectionKey.LOCATION,
            SectionKey.INSTRUCTORS,
            SectionKey.VALUE_STACK,
            SectionKey.TESTIMONIALS,
            SectionKey.PORTFOLIO,
            SectionKey.FAQ,
            SectionKey.GALLERY,
            SectionKey.RESOURCES,
            SectionKey.PRICING,
            SectionKey.CLOSING,
            SectionKey.KNOWLEDGE,
        ),
    ),
    OfferArchetype.PRODUCTO: ArchetypeCapabilities(
        archetype=OfferArchetype.PRODUCTO,
        # Sprint 15.1: PRODUCTO is promoted to supports_editions=True so
        # ecommerce tenants can model SKU variants (talla / color / material).
        # Offers without variants remain legitimate — ``allow_single_variant``
        # lets the UX collapse the 1-SKU case to the direct editor.
        supports_editions=True,
        edition_noun_es="variante",
        edition_noun_plural_es="variantes",
        requires_start_date_on_publish=False,
        requires_end_date_on_publish=False,
        requires_location_on_publish=False,
        supports_capacity=True,  # SKU inventory
        supports_waitlist=False,
        default_delivery=OfferDeliveryModel.DIY,
        default_fulfillment=FulfillmentType.DIGITAL_DOWNLOAD,
        default_variant_structure=VariantStructure.SKU_VARIANT,
        supported_variant_structures=(
            VariantStructure.SKU_VARIANT,
            VariantStructure.REGIONAL,
            VariantStructure.LANGUAGE,
        ),
        allow_single_variant=True,
        label_es="Producto",
        subtitle_es="Algo que creas y empaquetas",
        icon_name="Package",
        examples_es=(
            "Ebook",
            "Curso grabado",
            "Template",
            "Guía",
            "Producto físico",
        ),
        editions_wizard_title_es="¿Tiene variantes (talla, color, material, formato)?",
        editions_wizard_description_es=(
            "Las variantes son versiones del mismo producto que se diferencian por atributos. "
            "Cada variante tiene su propio SKU e inventario."
        ),
        editions_wizard_yes_label_es="Sí, tengo variantes",
        editions_wizard_no_label_es="No, es un producto único",
        sections=(
            SectionKey.IDENTITY,
            SectionKey.STRATEGY,
            SectionKey.PSYCHOLOGY,
            SectionKey.PROMISE,
            SectionKey.PRODUCT_DETAILS,
            SectionKey.VALUE_STACK,
            SectionKey.TESTIMONIALS,
            SectionKey.FAQ,
            SectionKey.GALLERY,
            SectionKey.RESOURCES,
            SectionKey.PRICING,
            SectionKey.CLOSING,
            SectionKey.KNOWLEDGE,
        ),
    ),
    OfferArchetype.MEMBRESIA: ArchetypeCapabilities(
        archetype=OfferArchetype.MEMBRESIA,
        # Sprint 15.1: MEMBRESIA is promoted to supports_editions=True so
        # membership tenants can model tier plans (Gold / Platinum / Enterprise).
        # ``allow_single_variant`` keeps the "one plan" case ceremony-free
        # when a tenant runs a flat-priced membership.
        supports_editions=True,
        edition_noun_es="plan",
        edition_noun_plural_es="planes",
        requires_start_date_on_publish=False,
        requires_end_date_on_publish=False,
        requires_location_on_publish=False,
        supports_capacity=True,  # per-plan seat caps (mastermind, enterprise)
        supports_waitlist=False,
        default_delivery=OfferDeliveryModel.DIY,
        default_fulfillment=FulfillmentType.LMS_ACCESS,
        default_variant_structure=VariantStructure.TIER,
        supported_variant_structures=(
            VariantStructure.TIER,
            VariantStructure.MODALITY,
            VariantStructure.LANGUAGE,
            VariantStructure.REGIONAL,
        ),
        allow_single_variant=True,
        label_es="Membresía",
        subtitle_es="Acceso continuo por suscripción",
        icon_name="RefreshCw",
        examples_es=(
            "Comunidad premium",
            "Newsletter paga",
            "Mastermind",
            "Club",
        ),
        editions_wizard_title_es="¿Tiene distintos planes o niveles?",
        editions_wizard_description_es=(
            "Los planes son niveles paralelos de la misma membresía con precio y beneficios "
            "distintos (Básico, Premium, Enterprise)."
        ),
        editions_wizard_yes_label_es="Sí, tengo varios planes",
        editions_wizard_no_label_es="No, es un plan único",
        sections=(
            SectionKey.IDENTITY,
            SectionKey.STRATEGY,
            SectionKey.PSYCHOLOGY,
            SectionKey.PROMISE,
            SectionKey.SUBSCRIPTION_DETAILS,
            SectionKey.PLATFORM_DETAILS,
            SectionKey.LOCATION,
            SectionKey.VALUE_STACK,
            SectionKey.TESTIMONIALS,
            SectionKey.FAQ,
            SectionKey.GALLERY,
            SectionKey.RESOURCES,
            SectionKey.PRICING,
            SectionKey.CLOSING,
            SectionKey.KNOWLEDGE,
        ),
    ),
}


def get_capabilities(archetype: OfferArchetype) -> ArchetypeCapabilities:
    """Return the capabilities record for ``archetype``.

    Raises :class:`KeyError` at import time through the architecture test if
    the catalog is ever missing an entry, so in practice this lookup cannot
    fail in running code.
    """
    return ARCHETYPE_CATALOG[archetype]
