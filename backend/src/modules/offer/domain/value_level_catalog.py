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

    Fields beyond the enum value capture why the rung exists (``role_in_funnel_es``),
    what the user should price it at (``typical_price_min_usd``/``typical_price_max_usd``
    for paid rungs; ``is_free=True`` for lead magnets), and how to render it
    (``icon_name``, ``label_es``, ``description_es``, ``examples_es``).

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
        label_es="Lead Magnet",
        description_es=(
            "Recurso gratuito que entregas a cambio del contacto. Su trabajo es captar leads calificados, no vender."
        ),
        role_in_funnel_es="Capta prospectos cualificados en la parte más ancha del funnel",
        icon_name="Lightbulb",
        examples_es=(
            "Ebook gratuito",
            "Webinar de valor",
            "Plantilla descargable",
            "Mini-curso por email",
        ),
        is_free=True,
    ),
    OfferValueLevel.ACTIVACION: ValueLevelMetadata(
        value_level=OfferValueLevel.ACTIVACION,
        order=1,
        label_es="Activación",
        description_es=(
            "Primera compra de bajo riesgo que convierte al lead en cliente. "
            "El ticket es accesible para activar la relación comercial."
        ),
        role_in_funnel_es="Convierte lead en cliente por primera vez con bajo compromiso",
        icon_name="Rocket",
        examples_es=(
            "Tripwire / oferta inicial",
            "Curso auto-dirigido económico",
            "Masterclass intensiva",
            "Kit de plantillas",
        ),
        typical_price_min_usd=17.0,
        typical_price_max_usd=97.0,
    ),
    OfferValueLevel.TRANSFORMACION: ValueLevelMetadata(
        value_level=OfferValueLevel.TRANSFORMACION,
        order=2,
        label_es="Transformación",
        description_es=(
            "Oferta principal del negocio. Entrega la transformación completa y concentra la mayor parte del revenue."
        ),
        role_in_funnel_es="Entrega la transformación central y genera el core del revenue",
        icon_name="TrendingUp",
        examples_es=(
            "Programa cohorte / bootcamp",
            "Mentoría grupal",
            "Certificación",
            "Retainer mensual",
        ),
        typical_price_min_usd=297.0,
        typical_price_max_usd=2997.0,
    ),
    OfferValueLevel.MAXIMIZACION: ValueLevelMetadata(
        value_level=OfferValueLevel.MAXIMIZACION,
        order=3,
        label_es="Maximización",
        description_es=(
            "Oferta premium de alto contacto para clientes que quieren el nivel más alto de acompañamiento o acceso."
        ),
        role_in_funnel_es="Maximiza el lifetime value de los clientes más comprometidos",
        icon_name="Gem",
        examples_es=(
            "Mentoría 1:1 premium",
            "VIP Day",
            "Mastermind exclusivo",
            "Retiro inmersivo",
        ),
        typical_price_min_usd=3000.0,
        typical_price_max_usd=30000.0,
    ),
    OfferValueLevel.CORPORATIVO: ValueLevelMetadata(
        value_level=OfferValueLevel.CORPORATIVO,
        order=4,
        label_es="Corporativo",
        description_es=(
            "Venta B2B a empresas o equipos. Ticket alto con proceso de venta consultiva y contratos formales."
        ),
        role_in_funnel_es="Venta B2B enterprise — ticket alto, proceso consultivo",
        icon_name="Building2",
        examples_es=(
            "Capacitación corporativa",
            "Patrocinios enterprise",
            "Licenciamiento white-label",
            "Consultoría in-company",
        ),
        typical_price_min_usd=5000.0,
        typical_price_max_usd=100000.0,
    ),
}


def get_value_level_metadata(value_level: OfferValueLevel) -> ValueLevelMetadata:
    """Return the metadata record for ``value_level``.

    The architecture test ``test_value_level_catalog_completeness``
    guarantees every enum value has an entry, so in practice this lookup
    cannot raise at runtime.
    """
    return VALUE_LEVEL_CATALOG[value_level]
