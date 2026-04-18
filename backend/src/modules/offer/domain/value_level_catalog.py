"""OfferValueLevel catalog — SSoT for the ladder rungs.

The five value levels (``LEAD_MAGNET`` → ``ACTIVACION`` → ``TRANSFORMACION``
→ ``MAXIMIZACION`` → ``CORPORATIVO``) form the canonical value ladder used
across the Offer Studio dashboard (grouping into streams), the create-offer
wizard (explicit rung selection), the ladder completeness scoring, and
analytics reports.

The enum lives in ``enums.py`` for backwards compatibility. The metadata
catalog lives here so the frontend stops hardcoding icons, labels, and
descriptions in individual components — a single frozen record per rung
keeps the UI coherent and the domain documentation in one place.

Labels, copy, and example offers are tuned for Latam mass-market so a
dentist, a gym owner, a coach or an indie SaaS founder can all recognise
the rung at a glance. Per-business-type adaptation lives in a separate
catalog (``offer_ladder_hints.py``) to keep this module pure-base in the
DAG (no outbound references to other catalogs or to ExpertBusinessType).

The catalog is not tenant-scoped and does not persist anywhere else: it
is a domain invariant. Adding a new rung implies code changes (dashboard
layout, funnel analytics, wizard copy), so an arch test guards drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.modules.offer.domain.enums import OfferValueLevel


@dataclass(frozen=True, slots=True)
class ValueLevelMetadata:
    """Localized presentation + funnel data for one rung of the value ladder.

    Fields beyond the enum value capture why the rung exists
    (``role_in_funnel_es``), what the user should price it at
    (``typical_price_min_usd``/``typical_price_max_usd`` for paid rungs;
    ``is_free=True`` for lead magnets), and how to render it (``icon_name``,
    ``label_es``, ``description_es``, ``examples_es``).

    ``examples_es`` holds **universal** example offer types. Tenant-
    contextualized examples (e.g. "Primera consulta promocional" for a
    dentist) live in ``OFFER_LADDER_HINTS`` keyed by
    ``(ExpertBusinessType, OfferValueLevel)``.

    ``order`` drives left-to-right ladder layout and analytics sorting.
    """

    value_level: OfferValueLevel
    order: int  # 0..N-1 contiguous; 0 = top of funnel
    label_es: str
    description_es: str
    role_in_funnel_es: str
    icon_name: str  # Lucide React PascalCase
    examples_es: tuple[str, ...] = field(default_factory=tuple)

    is_free: bool = False
    typical_price_min_usd: float | None = None
    typical_price_max_usd: float | None = None


VALUE_LEVEL_CATALOG: dict[OfferValueLevel, ValueLevelMetadata] = {
    OfferValueLevel.LEAD_MAGNET: ValueLevelMetadata(
        value_level=OfferValueLevel.LEAD_MAGNET,
        order=0,
        label_es="Gancho",
        description_es=(
            "Recurso o experiencia gratuita que entregás a cambio del contacto. "
            "Su trabajo es captar leads calificados y abrir la conversación — "
            "no vender."
        ),
        role_in_funnel_es="Capta prospectos cualificados",
        icon_name="Lightbulb",
        examples_es=(
            "Ebook gratuito",
            "Webinar de valor",
            "Masterclass gratis",
            "Plantilla descargable",
            "Diagnóstico gratuito",
            "Mini-curso por email",
        ),
        is_free=True,
    ),
    OfferValueLevel.ACTIVACION: ValueLevelMetadata(
        value_level=OfferValueLevel.ACTIVACION,
        order=1,
        label_es="Primera Compra",
        description_es=(
            "Primera compra de bajo riesgo que convierte al lead en cliente. "
            "El ticket es accesible — el objetivo es activar la relación "
            "comercial, no maximizar el margen."
        ),
        role_in_funnel_es="Convierte lead en cliente",
        icon_name="Rocket",
        examples_es=(
            "Tripwire $9-47",
            "Mini-curso económico",
            "Masterclass paga",
            "PDF premium",
            "Pase de prueba",
            "Primera consulta accesible",
        ),
        typical_price_min_usd=7.0,
        typical_price_max_usd=97.0,
    ),
    OfferValueLevel.TRANSFORMACION: ValueLevelMetadata(
        value_level=OfferValueLevel.TRANSFORMACION,
        order=2,
        label_es="Oferta Principal",
        description_es=(
            "Tu oferta principal. Entrega la transformación completa que "
            "prometés y concentra el grueso de tu revenue mensual."
        ),
        role_in_funnel_es="Entrega la transformación central",
        icon_name="TrendingUp",
        examples_es=(
            "Curso insignia $297-997",
            "Bootcamp / cohorte",
            "Mentoría grupal",
            "Paquete de tratamiento",
            "Retainer mensual",
            "Membresía premium",
        ),
        typical_price_min_usd=97.0,
        typical_price_max_usd=1997.0,
    ),
    OfferValueLevel.MAXIMIZACION: ValueLevelMetadata(
        value_level=OfferValueLevel.MAXIMIZACION,
        order=3,
        label_es="Premium",
        description_es=(
            "Oferta premium de alto contacto. Para los clientes más comprometidos "
            "que pagan por el nivel máximo de acceso, personalización o "
            "acompañamiento."
        ),
        role_in_funnel_es="Maximiza el valor por cliente top",
        icon_name="Gem",
        examples_es=(
            "Mentoría 1:1 premium",
            "Mastermind exclusivo",
            "VIP Day",
            "Retiro inmersivo",
            "Consultoría senior",
            "Programa white-glove",
        ),
        typical_price_min_usd=2000.0,
        typical_price_max_usd=20000.0,
    ),
    OfferValueLevel.CORPORATIVO: ValueLevelMetadata(
        value_level=OfferValueLevel.CORPORATIVO,
        order=4,
        label_es="Venta B2B",
        description_es=(
            "Venta B2B a empresas, aseguradoras o equipos. Ticket alto, proceso "
            "consultivo y contrato formal — ciclo de venta largo pero revenue "
            "predecible."
        ),
        role_in_funnel_es="Venta consultiva a empresas",
        icon_name="Building2",
        examples_es=(
            "Capacitación interna",
            "Licenciamiento white-label",
            "Consultoría in-company",
            "Programa para equipos",
            "Retainer corporativo",
            "Contrato institucional",
        ),
        typical_price_min_usd=5000.0,
        typical_price_max_usd=50000.0,
    ),
}


def get_value_level_metadata(value_level: OfferValueLevel) -> ValueLevelMetadata:
    """Return the metadata record for ``value_level``.

    The architecture test ``test_value_level_catalog_completeness``
    guarantees every enum value has an entry, so in practice this lookup
    cannot raise at runtime.
    """
    return VALUE_LEVEL_CATALOG[value_level]
