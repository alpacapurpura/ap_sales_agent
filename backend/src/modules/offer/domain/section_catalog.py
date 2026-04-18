"""Section Catalog — single source of truth for Offer Studio editor sections.

This module is the 5th SSoT axis of the offer-studio catalog system (see
``.claude/rules/offer-catalogs.md``), sitting alongside OfferArchetype,
OfferValueLevel, OfferFormat, and ExpertBusinessType. It declares:

- every section the offer-studio editor can render (``SectionKey``);
- the Spanish copy, icon, and persistence scope of each section
  (``SectionMetadata``);
- how each section relates to the Offer vs LaunchEdition aggregates
  (``SectionScope``).

The frontend ``features/offer-studio/schemas/`` directory consumes this
catalog via ``GET /api/v1/offer/archetypes/catalog`` (extended in Phase A.5
of ``SPRINT-6-PLAN.md``). Hardcoding section metadata on the frontend is
forbidden — the architecture test
``frontend/src/__tests__/architecture/test-no-section-catalog-duplicates.test.ts``
enforces this.

Architecture invariant: every ``SectionKey`` enum member MUST have a
matching ``SECTION_CATALOG`` entry, enforced by
``tests/architecture/test_section_catalog_completeness.py``. Every archetype
MUST declare which sections it surfaces via
``ArchetypeCapabilities.sections`` (added in Phase A.3), and the union of
those keys MUST be a subset of ``SectionKey``.

See ``DECISIONS.md`` sections D21-D25 for the rationale. See ``SPRINT-6-PLAN.md``
§Phase A for the execution plan this module implements.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SectionKey(StrEnum):
    """Stable identifier for an Offer Studio editor section.

    Values match the frontend ``SECTION_REGISTRY`` keys verbatim so URL
    segments, schema filenames, and copilot route-tool maps align without
    per-layer translation tables.
    """

    IDENTITY = "identity"
    STRATEGY = "strategy"
    PSYCHOLOGY = "psychology"
    PROMISE = "promise"
    VALUE_STACK = "value_stack"
    INSTRUCTORS = "instructors"
    KNOWLEDGE = "knowledge"
    CLOSING = "closing"
    PRODUCT_DETAILS = "product_details"
    SUBSCRIPTION_DETAILS = "subscription_details"
    GALLERY = "gallery"
    EVENT_DETAILS = "event_details"
    PRICING = "pricing"
    PROGRAM_DETAILS = "program_details"
    SERVICE_DETAILS = "service_details"
    RESOURCES = "resources"


class SectionScope(StrEnum):
    """Which aggregate a section's fields persist to.

    - ``OFFER_LEVEL``: fields live on the ``Offer`` row. Content is shared
      across all launches of the offer. Visible on both the virtual
      ``/edition/evergreen/`` URL and every specific-edition URL.
    - ``EDITION_LEVEL``: fields live on a ``LaunchEdition`` row. Visible
      only on specific-edition URLs; hidden under ``evergreen``.
    - ``MIXED``: per-field ``owner`` split (some fields on ``Offer``, others
      on ``LaunchEdition``). The form-runtime dispatcher routes saves based
      on the field's declared ``owner``.
    """

    OFFER_LEVEL = "offer_level"
    EDITION_LEVEL = "edition_level"
    MIXED = "mixed"


@dataclass(frozen=True, slots=True)
class SectionMetadata:
    """Frozen record describing a single offer-studio editor section.

    All fields are user-facing metadata plus the machine-readable
    ``scope``. Changes to Spanish copy roll out on catalog version bump;
    changes to ``scope`` MUST be paired with frontend schema updates
    (the ``owner`` declarations must still type-check). The dataclass is
    frozen to prevent drift between catalog reads inside a process.
    """

    key: SectionKey
    label_es: str
    subtitle_es: str
    icon_name: str  # Lucide PascalCase icon name, resolved on the frontend.
    scope: SectionScope


SECTION_CATALOG: dict[SectionKey, SectionMetadata] = {
    SectionKey.IDENTITY: SectionMetadata(
        key=SectionKey.IDENTITY,
        label_es="Identidad de oferta",
        subtitle_es="Nombre público, claim y posicionamiento en el mercado",
        icon_name="Fingerprint",
        scope=SectionScope.OFFER_LEVEL,
    ),
    SectionKey.STRATEGY: SectionMetadata(
        key=SectionKey.STRATEGY,
        label_es="Estrategia y avatar",
        subtitle_es="Para quién es esta oferta y qué problema resuelve",
        icon_name="Target",
        scope=SectionScope.OFFER_LEVEL,
    ),
    SectionKey.PSYCHOLOGY: SectionMetadata(
        key=SectionKey.PSYCHOLOGY,
        label_es="Psicología y motores de compra",
        subtitle_es="Objeciones, creencias y disparadores de decisión del avatar",
        icon_name="Brain",
        scope=SectionScope.OFFER_LEVEL,
    ),
    SectionKey.PROMISE: SectionMetadata(
        key=SectionKey.PROMISE,
        label_es="Promesa y resultado",
        subtitle_es="Transformación concreta que se compromete con el cliente",
        icon_name="Star",
        scope=SectionScope.OFFER_LEVEL,
    ),
    SectionKey.VALUE_STACK: SectionMetadata(
        key=SectionKey.VALUE_STACK,
        label_es="Stack de valor",
        subtitle_es="Componentes entregables que justifican el precio",
        icon_name="Layers",
        scope=SectionScope.OFFER_LEVEL,
    ),
    SectionKey.INSTRUCTORS: SectionMetadata(
        key=SectionKey.INSTRUCTORS,
        label_es="Instructores y autoridad",
        subtitle_es="Personas que respaldan la oferta con su experiencia",
        icon_name="Users",
        scope=SectionScope.OFFER_LEVEL,
    ),
    SectionKey.KNOWLEDGE: SectionMetadata(
        key=SectionKey.KNOWLEDGE,
        label_es="Conocimiento",
        subtitle_es="Documentos y materiales que alimentan al agente de ventas",
        icon_name="Database",
        scope=SectionScope.OFFER_LEVEL,
    ),
    SectionKey.CLOSING: SectionMetadata(
        key=SectionKey.CLOSING,
        label_es="Cierre y garantía",
        subtitle_es="Política de devolución, urgencia y último empujón",
        icon_name="CheckCircle",
        scope=SectionScope.OFFER_LEVEL,
    ),
    SectionKey.PRODUCT_DETAILS: SectionMetadata(
        key=SectionKey.PRODUCT_DETAILS,
        label_es="Detalles del producto",
        subtitle_es="Formato, entrega y características del producto digital o físico",
        icon_name="Package",
        scope=SectionScope.OFFER_LEVEL,
    ),
    SectionKey.SUBSCRIPTION_DETAILS: SectionMetadata(
        key=SectionKey.SUBSCRIPTION_DETAILS,
        label_es="Detalles de suscripción",
        subtitle_es="Ciclo de facturación, duración de acceso y beneficios",
        icon_name="RefreshCw",
        scope=SectionScope.OFFER_LEVEL,
    ),
    SectionKey.GALLERY: SectionMetadata(
        key=SectionKey.GALLERY,
        label_es="Galería visual",
        subtitle_es="Imágenes y recursos visuales para assets y landing",
        icon_name="Image",
        scope=SectionScope.OFFER_LEVEL,
    ),
    SectionKey.EVENT_DETAILS: SectionMetadata(
        key=SectionKey.EVENT_DETAILS,
        label_es="Detalles del evento",
        subtitle_es="Fecha, ubicación y capacidad de esta salida específica",
        icon_name="Calendar",
        scope=SectionScope.EDITION_LEVEL,
    ),
    SectionKey.PRICING: SectionMetadata(
        key=SectionKey.PRICING,
        label_es="Precios",
        subtitle_es="Precio base de la oferta y overrides por edición",
        icon_name="DollarSign",
        scope=SectionScope.MIXED,
    ),
    SectionKey.PROGRAM_DETAILS: SectionMetadata(
        key=SectionKey.PROGRAM_DETAILS,
        label_es="Detalles del programa",
        subtitle_es="Estructura del programa y ajustes por cohorte",
        icon_name="BookOpen",
        scope=SectionScope.MIXED,
    ),
    SectionKey.SERVICE_DETAILS: SectionMetadata(
        key=SectionKey.SERVICE_DETAILS,
        label_es="Detalles del servicio",
        subtitle_es="Modalidad de trabajo y fechas de convocatoria",
        icon_name="Briefcase",
        scope=SectionScope.MIXED,
    ),
    SectionKey.RESOURCES: SectionMetadata(
        key=SectionKey.RESOURCES,
        label_es="Recursos",
        subtitle_es="Material base de la oferta y recursos extra por edición",
        icon_name="Library",
        scope=SectionScope.MIXED,
    ),
}


def get_section(key: SectionKey) -> SectionMetadata:
    """Return the metadata record for ``key``.

    Raises ``KeyError`` when the catalog is missing an entry. Under the
    architecture test ``test_every_section_key_has_a_catalog_entry`` this
    branch cannot be reached at runtime — enum values and catalog keys are
    kept aligned by CI.
    """
    return SECTION_CATALOG[key]
