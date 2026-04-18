"""Section Catalog — single source of truth for Offer Studio editor sections.

This module is the 5th SSoT axis of the offer-studio catalog system (see
``.claude/rules/offer-catalogs.md``), sitting alongside OfferArchetype,
OfferValueLevel, OfferFormat, and ExpertBusinessType. It declares:

- every section the offer-studio editor can render (``SectionKey``);
- the Spanish copy, icon, and persistence scope of each section
  (``SectionMetadata``);
- how each section relates to the Offer vs LaunchEdition aggregates
  (``SectionScope``);
- how much the section weighs in offer completeness scoring
  (``completion_weight``);
- whether publishing is gated on the section being filled
  (``required_to_publish``);
- an extended help text shown in tooltips and onboarding
  (``help_text_es``).

The frontend ``features/offer-studio/schemas/`` directory consumes this
catalog via ``GET /api/v1/offer/archetypes/catalog`` (extended in Phase A.5
of ``SPRINT-6-PLAN.md``). Hardcoding section metadata on the frontend is
forbidden — ``.claude/rules/offer-catalogs.md`` spells out the rule and
the anti-drift arch test enforces it. Labels + subtitles are tuned for
Latam mass-market: an abogado, a dentist, a gym owner or an academia
founder should recognise every section's purpose without needing marketer
vocabulary ("avatar", "claim", "stack").

Icons are unique per section — cross-catalog collisions with archetypes,
variants, formats, or value levels are avoided so the UI never shows the
same glyph twice in a single surface.

Architecture invariant: every ``SectionKey`` enum member MUST have a
matching ``SECTION_CATALOG`` entry, enforced by
``tests/architecture/test_section_catalog_completeness.py``. Every archetype
MUST declare which sections it surfaces via
``ArchetypeCapabilities.sections`` (added in Phase A.3), and the union of
those keys MUST be a subset of ``SectionKey``.

See ``DECISIONS.md`` sections D21-D25 for the original scope decisions.
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

    All fields are user-facing metadata plus machine-readable flags.
    Changes to Spanish copy roll out on catalog version bump; changes to
    ``scope`` MUST be paired with frontend schema updates (the ``owner``
    declarations must still type-check). The dataclass is frozen to
    prevent drift between catalog reads inside a process.
    """

    key: SectionKey
    # --- User-facing copy (Spanish, Latam mass-market tone) -----------------
    label_es: str
    subtitle_es: str
    # Extended help shown in tooltips and onboarding tours — explains WHY
    # this section matters and HOW it connects to the rest of the system
    # (sales agent, landing, analytics). Kept to 1-2 sentences so the UI
    # can render it inline without breaking card layouts.
    help_text_es: str
    icon_name: str  # Lucide PascalCase icon name, resolved on the frontend.

    # --- Persistence + editor mechanics -------------------------------------
    scope: SectionScope
    # Weight in the per-offer completeness score (0.0..1.0). 1.0 = critical
    # for a credible offer; 0.3 = polish-only. Consumer logic divides the
    # sum of weights across completed sections by the sum across all
    # applicable sections to compute the percentage. Keeping this in the
    # catalog (not per-tenant) makes the score comparable across tenants
    # for benchmarking without leaking tenant strategy.
    completion_weight: float
    # True when the section being empty blocks offer publishing. Applied
    # only to sections the archetype actually surfaces — archetypes that
    # don't include a required section simply skip its gate (e.g.
    # ``PROGRAMA`` doesn't surface ``PRODUCT_DETAILS`` so it's never
    # enforced there).
    required_to_publish: bool


SECTION_CATALOG: dict[SectionKey, SectionMetadata] = {
    SectionKey.IDENTITY: SectionMetadata(
        key=SectionKey.IDENTITY,
        label_es="Identidad de la oferta",
        subtitle_es="Nombre público, frase corta y posicionamiento",
        help_text_es=(
            "Define cómo se presenta tu oferta en anuncios, landings y checkout. "
            "Un nombre claro y una frase memorable facilitan que tu prospecto "
            "entienda qué vendés en 3 segundos."
        ),
        icon_name="Fingerprint",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=1.0,
        required_to_publish=True,
    ),
    SectionKey.STRATEGY: SectionMetadata(
        key=SectionKey.STRATEGY,
        label_es="Estrategia y cliente ideal",
        subtitle_es="Para quién es la oferta y qué problema resuelve",
        help_text_es=(
            "Quién es tu cliente ideal, qué problema enfrenta y por qué tu oferta "
            "es la respuesta. El agente de ventas usa esto para calificar leads y "
            "conectar en el lenguaje del cliente."
        ),
        icon_name="Target",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.9,
        required_to_publish=True,
    ),
    SectionKey.PSYCHOLOGY: SectionMetadata(
        key=SectionKey.PSYCHOLOGY,
        label_es="Motivaciones y objeciones",
        subtitle_es="Qué frena a tu cliente y qué lo empuja a comprar",
        help_text_es=(
            "Los miedos, creencias y disparadores emocionales del cliente antes "
            "de decidir. El agente de ventas responde objeciones en tiempo real "
            "apoyándose en este mapa."
        ),
        icon_name="HeartPulse",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.7,
        required_to_publish=False,
    ),
    SectionKey.PROMISE: SectionMetadata(
        key=SectionKey.PROMISE,
        label_es="Promesa y resultado",
        subtitle_es="Transformación concreta que le garantizás al cliente",
        help_text_es=(
            "El antes y el después que comprometés con tu cliente. Tiene que ser "
            "concreto, medible y plausible — es la promesa central de tu marketing "
            "y del contrato implícito con quien compra."
        ),
        icon_name="Star",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=1.0,
        required_to_publish=True,
    ),
    SectionKey.VALUE_STACK: SectionMetadata(
        key=SectionKey.VALUE_STACK,
        label_es="Valor entregado",
        subtitle_es="Qué recibe exactamente el cliente al comprar",
        help_text_es=(
            "Lista enumerada de todo lo que el cliente recibe: módulos, sesiones, "
            "materiales, accesos. Cuanto más concreto, más fácil justificar el "
            "precio y comparar contra alternativas."
        ),
        icon_name="Gift",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.8,
        required_to_publish=False,
    ),
    SectionKey.INSTRUCTORS: SectionMetadata(
        key=SectionKey.INSTRUCTORS,
        label_es="Equipo y autoridad",
        subtitle_es="Quién respalda la oferta con su experiencia",
        help_text_es=(
            "Personas que dictan, facilitan o respaldan la oferta. Credenciales, "
            "logros y presencia mediática: la autoridad del equipo se convierte "
            "en confianza del prospecto."
        ),
        icon_name="BadgeCheck",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.5,
        required_to_publish=False,
    ),
    SectionKey.KNOWLEDGE: SectionMetadata(
        key=SectionKey.KNOWLEDGE,
        label_es="Base de conocimiento",
        subtitle_es="Documentos que alimentan al agente de ventas",
        help_text_es=(
            "Documentos, PDFs y guiones que el agente de ventas consulta para "
            "responder preguntas técnicas sobre tu oferta. A mayor cobertura "
            "documental, menos escalamientos humanos."
        ),
        icon_name="Database",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.6,
        required_to_publish=False,
    ),
    SectionKey.CLOSING: SectionMetadata(
        key=SectionKey.CLOSING,
        label_es="Cierre y garantía",
        subtitle_es="Garantía, urgencia y empuje final para cerrar",
        help_text_es=(
            "Los elementos que disparan la decisión final: garantía de devolución, "
            "escasez real, bonos que caducan. Diseñalos para bajar el riesgo "
            "percibido sin caer en presión falsa."
        ),
        icon_name="CheckCircle",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.7,
        required_to_publish=False,
    ),
    SectionKey.PRODUCT_DETAILS: SectionMetadata(
        key=SectionKey.PRODUCT_DETAILS,
        label_es="Detalles del producto",
        subtitle_es="Formato, entrega y características del producto",
        help_text_es=(
            "Especificaciones del producto que vendés: formato (PDF, video, físico), "
            "peso, duración, acceso, restricciones. El agente de ventas usa estos "
            "datos para responder dudas técnicas antes de la compra."
        ),
        icon_name="PackageOpen",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.9,
        required_to_publish=True,
    ),
    SectionKey.SUBSCRIPTION_DETAILS: SectionMetadata(
        key=SectionKey.SUBSCRIPTION_DETAILS,
        label_es="Detalles de suscripción",
        subtitle_es="Ciclo de facturación, duración y beneficios",
        help_text_es=(
            "Reglas de la suscripción: ciclo (mensual/anual), renovación automática, "
            "cancelación, beneficios escalonados. Transparencia acá previene "
            "cancelaciones tempranas y disputas."
        ),
        icon_name="CreditCard",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.9,
        required_to_publish=True,
    ),
    SectionKey.GALLERY: SectionMetadata(
        key=SectionKey.GALLERY,
        label_es="Galería",
        subtitle_es="Imágenes y recursos visuales para assets y landing",
        help_text_es=(
            "Fotos, mockups e imágenes que usa el generador de landings y assets. "
            "Al menos una imagen principal de alta calidad mueve la aguja de "
            "conversión en la landing."
        ),
        icon_name="Image",
        scope=SectionScope.OFFER_LEVEL,
        completion_weight=0.4,
        required_to_publish=False,
    ),
    SectionKey.EVENT_DETAILS: SectionMetadata(
        key=SectionKey.EVENT_DETAILS,
        label_es="Detalles del evento",
        subtitle_es="Fecha, ubicación y capacidad de esta salida",
        help_text_es=(
            "Datos logísticos que cambian por edición: fecha, ubicación física o "
            "link de streaming, capacidad, idioma. Son los datos que el cliente "
            "necesita antes de comprar el ticket."
        ),
        icon_name="CalendarCheck",
        scope=SectionScope.EDITION_LEVEL,
        completion_weight=1.0,
        required_to_publish=True,
    ),
    SectionKey.PRICING: SectionMetadata(
        key=SectionKey.PRICING,
        label_es="Precios y pagos",
        subtitle_es="Precio base, cuotas y overrides por edición",
        help_text_es=(
            "Precio principal, moneda, opciones de pago (cuotas, early-bird), "
            "impuestos. Sin precio cargado no hay checkout — es el bloque que "
            "bloquea la publicación si queda vacío."
        ),
        icon_name="DollarSign",
        scope=SectionScope.MIXED,
        completion_weight=1.0,
        required_to_publish=True,
    ),
    SectionKey.PROGRAM_DETAILS: SectionMetadata(
        key=SectionKey.PROGRAM_DETAILS,
        label_es="Detalles del programa",
        subtitle_es="Estructura del programa y ajustes por cohorte",
        help_text_es=(
            "Cómo se desarrolla el programa: módulos, sesiones, recorrido, carga "
            "semanal, hitos clave. El cliente necesita visualizar el viaje completo "
            "antes de comprometerse."
        ),
        icon_name="Route",
        scope=SectionScope.MIXED,
        completion_weight=0.9,
        required_to_publish=True,
    ),
    SectionKey.SERVICE_DETAILS: SectionMetadata(
        key=SectionKey.SERVICE_DETAILS,
        label_es="Detalles del servicio",
        subtitle_es="Modalidad de trabajo y fechas de convocatoria",
        help_text_es=(
            "Cómo trabajás con el cliente: modalidad (1:1, grupal, híbrido), "
            "canales, disponibilidad, tiempos de respuesta. Define la experiencia "
            "práctica del servicio."
        ),
        icon_name="Briefcase",
        scope=SectionScope.MIXED,
        completion_weight=0.9,
        required_to_publish=True,
    ),
    SectionKey.RESOURCES: SectionMetadata(
        key=SectionKey.RESOURCES,
        label_es="Materiales y recursos",
        subtitle_es="Material base y bonus específicos por edición",
        help_text_es=(
            "Plantillas, PDFs, grabaciones y accesos a herramientas. Separá los "
            "recursos core (que se incluyen siempre) de los bonus específicos "
            "de cada edición."
        ),
        icon_name="FileStack",
        scope=SectionScope.MIXED,
        completion_weight=0.6,
        required_to_publish=False,
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
