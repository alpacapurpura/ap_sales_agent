"""OfferFormat catalog — SSoT for the descriptive "flavor" within each archetype.

The 25 entries describe common formats an expert business would sell
(ebook, masterclass, bootcamp, retainer, retreat, …). They serve the
Offer Studio wizard step where the tenant picks a format inside the
chosen archetype.

Design decisions (captured in docs/domains/offer/catalogs-consolidation.md):

- ``suggested_value_level`` is **intentionally absent**. The ladder rung
  is a separate, explicit decision in the wizard — pre-filling it from
  the format biased every offer and hid the choice.
- ``delivery_model`` is informative only (D2 — helps the user later see
  "what proportion of my offers are DIY vs DWY vs DFY"). It does not gate
  anything in the editor.
- ``suitable_for`` holds a ``dict[ExpertBusinessType, float]`` with scores
  in [0, 1]: 1.0 = primary fit, 0.5 = secondary (show with "menos común"
  badge), absent/0.0 = hidden. The wizard filters by intersection with
  ``BrandIdentity.business_types``.
- Every archetype ships a ``*_custom`` escape-hatch format that every
  business type can see (score 1.0 across the board). Enforced by arch
  test.

``format_id`` is persisted on the offer side as ``format_hint`` (plain
string), so the ID serves as both UI identity and analytics join key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.modules.offer.domain.enums import OfferArchetype, OfferDeliveryModel
from src.shared.domain.expert_business_type import ExpertBusinessType

_ALL_TYPES_PRIMARY: dict[ExpertBusinessType, float] = dict.fromkeys(ExpertBusinessType, 1.0)


@dataclass(frozen=True, slots=True)
class FormatMetadata:
    """Descriptive record for one offer format.

    ``format_id`` is a stable, archetype-prefixed slug (e.g.
    ``"programa_bootcamp"``) — used both as dict key and as the value
    persisted on offers for analytics joins. Never rename — add a new
    entry and deprecate the old one instead.
    """

    format_id: str
    archetype: OfferArchetype
    label_es: str
    description_es: str
    icon_name: str  # Lucide React PascalCase
    format_hint: str  # persisted on offer.format_hint; empty for custom
    delivery_model: OfferDeliveryModel
    suitable_for: dict[ExpertBusinessType, float]
    tags: tuple[str, ...] = field(default_factory=tuple)
    specific_details_defaults: dict[str, Any] = field(default_factory=dict)


_FORMATS: tuple[FormatMetadata, ...] = (
    # ── PRODUCTO ─────────────────────────────────────────────────────
    FormatMetadata(
        format_id="producto_ebook",
        archetype=OfferArchetype.PRODUCTO,
        label_es="Ebook / Guía",
        description_es="Contenido descargable que educa y posiciona tu expertise.",
        icon_name="BookOpen",
        format_hint="Ebook / Guía",
        delivery_model=OfferDeliveryModel.DIY,
        suitable_for={
            ExpertBusinessType.EDUCADOR_INFOPRODUCTOR: 1.0,
            ExpertBusinessType.CREADOR_CONTENIDO: 1.0,
            ExpertBusinessType.CONSULTOR_ASESOR: 1.0,
            ExpertBusinessType.COACH_MENTOR: 1.0,
            ExpertBusinessType.AGENCIA_DFY: 0.5,
            ExpertBusinessType.HOST_COMUNIDAD: 0.5,
            ExpertBusinessType.SAAS_FOUNDER: 0.5,
        },
        tags=("lead-magnet", "contenido", "digital"),
    ),
    FormatMetadata(
        format_id="producto_curso",
        archetype=OfferArchetype.PRODUCTO,
        label_es="Curso Grabado",
        description_es="Videos pregrabados con estructura modular y acceso inmediato.",
        icon_name="Video",
        format_hint="Curso Grabado",
        delivery_model=OfferDeliveryModel.DIY,
        suitable_for={
            ExpertBusinessType.EDUCADOR_INFOPRODUCTOR: 1.0,
            ExpertBusinessType.COACH_MENTOR: 1.0,
            ExpertBusinessType.CREADOR_CONTENIDO: 1.0,
            ExpertBusinessType.CONSULTOR_ASESOR: 0.5,
            ExpertBusinessType.SAAS_FOUNDER: 0.5,
        },
        tags=("curso", "video", "autodirigido"),
    ),
    FormatMetadata(
        format_id="producto_kit",
        archetype=OfferArchetype.PRODUCTO,
        label_es="Kit / Toolkit",
        description_es="Paquete de plantillas, checklists y recursos listos para usar.",
        icon_name="Package",
        format_hint="Kit / Toolkit",
        delivery_model=OfferDeliveryModel.DIY,
        suitable_for={
            ExpertBusinessType.EDUCADOR_INFOPRODUCTOR: 1.0,
            ExpertBusinessType.CONSULTOR_ASESOR: 1.0,
            ExpertBusinessType.AGENCIA_DFY: 1.0,
            ExpertBusinessType.SAAS_FOUNDER: 0.5,
            ExpertBusinessType.COACH_MENTOR: 0.5,
        },
        tags=("plantillas", "herramientas", "digital"),
    ),
    FormatMetadata(
        format_id="producto_fisico",
        archetype=OfferArchetype.PRODUCTO,
        label_es="Producto Físico",
        description_es="Producto tangible con envío y logística incluida.",
        icon_name="Box",
        format_hint="Producto Físico",
        delivery_model=OfferDeliveryModel.DIY,
        suitable_for={
            ExpertBusinessType.PRODUCT_MAKER: 1.0,
            ExpertBusinessType.CREADOR_CONTENIDO: 1.0,
            ExpertBusinessType.HOST_COMUNIDAD: 0.5,
        },
        tags=("físico", "envío", "tangible"),
    ),
    FormatMetadata(
        format_id="producto_custom",
        archetype=OfferArchetype.PRODUCTO,
        label_es="Personalizado",
        description_es="Define tu propio formato de producto.",
        icon_name="Settings",
        format_hint="",
        delivery_model=OfferDeliveryModel.DIY,
        suitable_for=_ALL_TYPES_PRIMARY,
        tags=("custom",),
    ),
    # ── PROGRAMA ─────────────────────────────────────────────────────
    FormatMetadata(
        format_id="programa_masterclass",
        archetype=OfferArchetype.PROGRAMA,
        label_es="Masterclass",
        description_es="Sesión intensiva de alto valor sobre un tema específico.",
        icon_name="Presentation",
        format_hint="Masterclass",
        delivery_model=OfferDeliveryModel.DWY,
        suitable_for={
            ExpertBusinessType.EDUCADOR_INFOPRODUCTOR: 1.0,
            ExpertBusinessType.COACH_MENTOR: 1.0,
            ExpertBusinessType.CONSULTOR_ASESOR: 1.0,
            ExpertBusinessType.CREADOR_CONTENIDO: 1.0,
            ExpertBusinessType.AGENCIA_DFY: 0.5,
            ExpertBusinessType.HOST_COMUNIDAD: 0.5,
        },
        tags=("live", "intensivo", "sesión"),
    ),
    FormatMetadata(
        format_id="programa_bootcamp",
        archetype=OfferArchetype.PROGRAMA,
        label_es="Bootcamp / Cohorte",
        description_es="Programa grupal con fechas fijas y entregables semanales.",
        icon_name="GraduationCap",
        format_hint="Bootcamp / Cohorte",
        delivery_model=OfferDeliveryModel.DWY,
        suitable_for={
            ExpertBusinessType.EDUCADOR_INFOPRODUCTOR: 1.0,
            ExpertBusinessType.COACH_MENTOR: 1.0,
            ExpertBusinessType.CONSULTOR_ASESOR: 0.5,
            ExpertBusinessType.CREADOR_CONTENIDO: 0.5,
        },
        tags=("cohorte", "grupal", "transformación"),
    ),
    FormatMetadata(
        format_id="programa_certificacion",
        archetype=OfferArchetype.PROGRAMA,
        label_es="Certificación",
        description_es="Programa formal con evaluación y credencial al completar.",
        icon_name="Award",
        format_hint="Certificación",
        delivery_model=OfferDeliveryModel.DWY,
        suitable_for={
            ExpertBusinessType.EDUCADOR_INFOPRODUCTOR: 1.0,
            ExpertBusinessType.CONSULTOR_ASESOR: 0.5,
            ExpertBusinessType.COACH_MENTOR: 0.5,
        },
        tags=("certificado", "formal", "credencial"),
    ),
    FormatMetadata(
        format_id="programa_evergreen",
        archetype=OfferArchetype.PROGRAMA,
        label_es="Curso Evergreen",
        description_es="Programa autodirigido disponible todo el año, sin cohorte.",
        icon_name="Infinity",
        format_hint="Curso Evergreen",
        delivery_model=OfferDeliveryModel.DIY,
        suitable_for={
            ExpertBusinessType.EDUCADOR_INFOPRODUCTOR: 1.0,
            ExpertBusinessType.CREADOR_CONTENIDO: 1.0,
            ExpertBusinessType.COACH_MENTOR: 0.5,
            ExpertBusinessType.CONSULTOR_ASESOR: 0.5,
            ExpertBusinessType.SAAS_FOUNDER: 0.5,
        },
        tags=("evergreen", "autodirigido", "escalable"),
    ),
    FormatMetadata(
        format_id="programa_custom",
        archetype=OfferArchetype.PROGRAMA,
        label_es="Personalizado",
        description_es="Define tu propio formato de programa.",
        icon_name="Settings",
        format_hint="",
        delivery_model=OfferDeliveryModel.DWY,
        suitable_for=_ALL_TYPES_PRIMARY,
        tags=("custom",),
    ),
    # ── SERVICIO ─────────────────────────────────────────────────────
    FormatMetadata(
        format_id="servicio_mentoria",
        archetype=OfferArchetype.SERVICIO,
        label_es="Mentoría 1:1",
        description_es="Acompañamiento personalizado con sesiones individuales.",
        icon_name="UserCheck",
        format_hint="Mentoría 1:1",
        delivery_model=OfferDeliveryModel.DFY,
        suitable_for={
            ExpertBusinessType.COACH_MENTOR: 1.0,
            ExpertBusinessType.CONSULTOR_ASESOR: 1.0,
            ExpertBusinessType.EDUCADOR_INFOPRODUCTOR: 0.5,
        },
        tags=("1on1", "mentoría", "premium"),
    ),
    FormatMetadata(
        format_id="servicio_dfy",
        archetype=OfferArchetype.SERVICIO,
        label_es="Servicio DFY",
        description_es="Tu equipo ejecuta todo: el cliente solo aprueba resultados.",
        icon_name="Wrench",
        format_hint="Servicio DFY",
        delivery_model=OfferDeliveryModel.DFY,
        suitable_for={
            ExpertBusinessType.AGENCIA_DFY: 1.0,
            ExpertBusinessType.SAAS_FOUNDER: 0.5,
        },
        tags=("done-for-you", "agencia", "ejecución"),
    ),
    FormatMetadata(
        format_id="servicio_vip_day",
        archetype=OfferArchetype.SERVICIO,
        label_es="VIP Day",
        description_es="Día intensivo dedicado a resolver un problema específico.",
        icon_name="Zap",
        format_hint="VIP Day",
        delivery_model=OfferDeliveryModel.DFY,
        suitable_for={
            ExpertBusinessType.CONSULTOR_ASESOR: 1.0,
            ExpertBusinessType.COACH_MENTOR: 1.0,
            ExpertBusinessType.AGENCIA_DFY: 1.0,
        },
        tags=("intensivo", "premium", "día"),
    ),
    FormatMetadata(
        format_id="servicio_retainer",
        archetype=OfferArchetype.SERVICIO,
        label_es="Retainer Mensual",
        description_es="Servicio mensual recurrente con horas o entregables fijos.",
        icon_name="CalendarClock",
        format_hint="Retainer Mensual",
        delivery_model=OfferDeliveryModel.DFY,
        suitable_for={
            ExpertBusinessType.AGENCIA_DFY: 1.0,
            ExpertBusinessType.CONSULTOR_ASESOR: 1.0,
            ExpertBusinessType.SAAS_FOUNDER: 0.5,
        },
        tags=("recurrente", "mensual", "retainer"),
    ),
    FormatMetadata(
        format_id="servicio_custom",
        archetype=OfferArchetype.SERVICIO,
        label_es="Personalizado",
        description_es="Define tu propio formato de servicio.",
        icon_name="Settings",
        format_hint="",
        delivery_model=OfferDeliveryModel.DFY,
        suitable_for=_ALL_TYPES_PRIMARY,
        tags=("custom",),
    ),
    # ── MEMBRESIA ────────────────────────────────────────────────────
    FormatMetadata(
        format_id="membresia_comunidad",
        archetype=OfferArchetype.MEMBRESIA,
        label_es="Comunidad",
        description_es="Espacio de networking y soporte continuo entre miembros.",
        icon_name="Users",
        format_hint="Comunidad",
        delivery_model=OfferDeliveryModel.DIY,
        suitable_for={
            ExpertBusinessType.HOST_COMUNIDAD: 1.0,
            ExpertBusinessType.EDUCADOR_INFOPRODUCTOR: 1.0,
            ExpertBusinessType.CREADOR_CONTENIDO: 1.0,
            ExpertBusinessType.COACH_MENTOR: 1.0,
            ExpertBusinessType.CONSULTOR_ASESOR: 0.5,
        },
        tags=("comunidad", "networking", "soporte"),
    ),
    FormatMetadata(
        format_id="membresia_biblioteca",
        archetype=OfferArchetype.MEMBRESIA,
        label_es="Biblioteca de Contenido",
        description_es="Acceso a una biblioteca creciente de contenido exclusivo.",
        icon_name="Library",
        format_hint="Biblioteca de Contenido",
        delivery_model=OfferDeliveryModel.DIY,
        suitable_for={
            ExpertBusinessType.EDUCADOR_INFOPRODUCTOR: 1.0,
            ExpertBusinessType.CREADOR_CONTENIDO: 1.0,
            ExpertBusinessType.CONSULTOR_ASESOR: 1.0,
            ExpertBusinessType.SAAS_FOUNDER: 0.5,
        },
        tags=("contenido", "biblioteca", "digital"),
    ),
    FormatMetadata(
        format_id="membresia_mastermind",
        archetype=OfferArchetype.MEMBRESIA,
        label_es="Mastermind",
        description_es="Grupo selecto con sesiones de estrategia y accountability.",
        icon_name="Brain",
        format_hint="Mastermind",
        delivery_model=OfferDeliveryModel.DWY,
        suitable_for={
            ExpertBusinessType.HOST_COMUNIDAD: 1.0,
            ExpertBusinessType.COACH_MENTOR: 1.0,
            ExpertBusinessType.CONSULTOR_ASESOR: 1.0,
        },
        tags=("mastermind", "estrategia", "grupal"),
    ),
    FormatMetadata(
        format_id="membresia_inner_circle",
        archetype=OfferArchetype.MEMBRESIA,
        label_es="Inner Circle",
        description_es="El nivel más exclusivo: acceso directo, eventos privados y más.",
        icon_name="Crown",
        format_hint="Inner Circle",
        delivery_model=OfferDeliveryModel.DWY,
        suitable_for={
            ExpertBusinessType.HOST_COMUNIDAD: 1.0,
            ExpertBusinessType.CONSULTOR_ASESOR: 1.0,
            ExpertBusinessType.CREADOR_CONTENIDO: 1.0,
            ExpertBusinessType.COACH_MENTOR: 0.5,
        },
        tags=("exclusivo", "vip", "premium"),
    ),
    FormatMetadata(
        format_id="membresia_custom",
        archetype=OfferArchetype.MEMBRESIA,
        label_es="Personalizado",
        description_es="Define tu propio formato de membresía.",
        icon_name="Settings",
        format_hint="",
        delivery_model=OfferDeliveryModel.DIY,
        suitable_for=_ALL_TYPES_PRIMARY,
        tags=("custom",),
    ),
    # ── EXPERIENCIA ──────────────────────────────────────────────────
    FormatMetadata(
        format_id="experiencia_retiro",
        archetype=OfferArchetype.EXPERIENCIA,
        label_es="Retiro Inmersivo",
        description_es="Experiencia inmersiva de varios días en un lugar especial.",
        icon_name="Mountain",
        format_hint="Retiro Inmersivo",
        delivery_model=OfferDeliveryModel.DWY,
        suitable_for={
            ExpertBusinessType.HOST_EXPERIENCIA: 1.0,
            ExpertBusinessType.COACH_MENTOR: 1.0,
            ExpertBusinessType.CREADOR_CONTENIDO: 0.5,
        },
        tags=("retiro", "inmersivo", "presencial"),
    ),
    FormatMetadata(
        format_id="experiencia_evento",
        archetype=OfferArchetype.EXPERIENCIA,
        label_es="Evento / Conferencia",
        description_es="Evento con speakers, networking y activaciones de marca.",
        icon_name="CalendarDays",
        format_hint="Evento / Conferencia",
        delivery_model=OfferDeliveryModel.DWY,
        suitable_for={
            ExpertBusinessType.HOST_EXPERIENCIA: 1.0,
            ExpertBusinessType.CREADOR_CONTENIDO: 1.0,
            ExpertBusinessType.EDUCADOR_INFOPRODUCTOR: 1.0,
            ExpertBusinessType.HOST_COMUNIDAD: 0.5,
        },
        tags=("evento", "conferencia", "speakers"),
    ),
    FormatMetadata(
        format_id="experiencia_taller",
        archetype=OfferArchetype.EXPERIENCIA,
        label_es="Taller Presencial",
        description_es="Workshop práctico donde los participantes aprenden haciendo.",
        icon_name="Hammer",
        format_hint="Taller Presencial",
        delivery_model=OfferDeliveryModel.DWY,
        suitable_for={
            ExpertBusinessType.EDUCADOR_INFOPRODUCTOR: 1.0,
            ExpertBusinessType.COACH_MENTOR: 1.0,
            ExpertBusinessType.HOST_EXPERIENCIA: 1.0,
            ExpertBusinessType.AGENCIA_DFY: 0.5,
        },
        tags=("taller", "presencial", "práctico"),
    ),
    FormatMetadata(
        format_id="experiencia_summit",
        archetype=OfferArchetype.EXPERIENCIA,
        label_es="Summit Virtual",
        description_es="Evento online con múltiples expertos y sesiones en vivo.",
        icon_name="Monitor",
        format_hint="Summit Virtual",
        delivery_model=OfferDeliveryModel.DIY,
        suitable_for={
            ExpertBusinessType.CREADOR_CONTENIDO: 1.0,
            ExpertBusinessType.EDUCADOR_INFOPRODUCTOR: 1.0,
            ExpertBusinessType.HOST_COMUNIDAD: 1.0,
            ExpertBusinessType.SAAS_FOUNDER: 0.5,
        },
        tags=("virtual", "summit", "online"),
    ),
    FormatMetadata(
        format_id="experiencia_custom",
        archetype=OfferArchetype.EXPERIENCIA,
        label_es="Personalizado",
        description_es="Define tu propio formato de experiencia.",
        icon_name="Settings",
        format_hint="",
        delivery_model=OfferDeliveryModel.DWY,
        suitable_for=_ALL_TYPES_PRIMARY,
        tags=("custom",),
    ),
)


FORMAT_CATALOG: dict[str, FormatMetadata] = {m.format_id: m for m in _FORMATS}


def get_format_metadata(format_id: str) -> FormatMetadata:
    """Return the metadata record for ``format_id``.

    Raises :class:`KeyError` if the format does not exist. Callers that
    accept legacy/arbitrary strings should use ``.get()`` on the catalog.
    """
    return FORMAT_CATALOG[format_id]


def format_ids_for_archetype(archetype: OfferArchetype) -> list[str]:
    """Return the ``format_id``s declared for ``archetype``, in catalog order."""
    return [m.format_id for m in _FORMATS if m.archetype is archetype]


def get_formats_suitable_for(
    business_types: list[ExpertBusinessType],
    archetype: OfferArchetype | None = None,
) -> list[FormatMetadata]:
    """Return formats relevant to the given business types, ranked by fit.

    An empty ``business_types`` means the tenant has not completed the
    Brand Studio onboarding step yet — in that case every format is
    returned (catalog order) so the wizard still works.

    When ``business_types`` is non-empty, a format is included iff it has
    a positive suitability score for at least one of the given types, and
    results are sorted by the best-matching score descending. ``archetype``
    narrows the result set when the wizard has already picked one.
    """
    base: list[FormatMetadata] = list(_FORMATS)
    if archetype is not None:
        base = [m for m in base if m.archetype is archetype]

    if not business_types:
        return base

    def best_score(meta: FormatMetadata) -> float:
        return max((meta.suitable_for.get(bt, 0.0) for bt in business_types), default=0.0)

    scored = [(best_score(m), m) for m in base]
    matching = [(score, m) for score, m in scored if score > 0]
    matching.sort(key=lambda pair: pair[0], reverse=True)
    return [m for _, m in matching]
