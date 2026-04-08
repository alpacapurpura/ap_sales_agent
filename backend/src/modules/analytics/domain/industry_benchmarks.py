"""Industry benchmark data for metric contextualization.

Pure domain module — no framework dependencies.
Data sourced from Klipfolio / MetricHQ industry averages.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IndustryCategory(str, Enum):
    """Broad industry verticals for benchmark segmentation."""

    EDUCATION = "education"
    ECOMMERCE = "ecommerce"
    SERVICES = "services"
    FITNESS = "fitness"
    SAAS = "saas"
    BEAUTY = "beauty"
    GENERAL = "general"


@dataclass(frozen=True)
class IndustryBenchmarkEntry:
    """A single benchmark data point for a metric within an industry."""

    metric_name: str
    low: float
    median: float
    high: float
    unit: str
    interpretation_es: str


# ---------------------------------------------------------------------------
# Benchmark lookup table
# ---------------------------------------------------------------------------

INDUSTRY_BENCHMARKS: dict[IndustryCategory, list[IndustryBenchmarkEntry]] = {
    IndustryCategory.GENERAL: [
        IndustryBenchmarkEntry(
            metric_name="CTR",
            low=0.9,
            median=1.5,
            high=2.19,
            unit="percentage",
            interpretation_es=(
                "CTR mide la efectividad de tus anuncios para generar clics"
            ),
        ),
        IndustryBenchmarkEntry(
            metric_name="CPC",
            low=0.70,
            median=1.20,
            high=1.72,
            unit="currency",
            interpretation_es="Costo por cada clic en tus anuncios",
        ),
        IndustryBenchmarkEntry(
            metric_name="CPL",
            low=15.0,
            median=27.66,
            high=45.0,
            unit="currency",
            interpretation_es="Costo por cada lead generado",
        ),
        IndustryBenchmarkEntry(
            metric_name="ROAS",
            low=1.93,
            median=2.0,
            high=2.19,
            unit="ratio",
            interpretation_es="Retorno por cada dolar invertido en ads",
        ),
        IndustryBenchmarkEntry(
            metric_name="CPA",
            low=20.0,
            median=38.17,
            high=55.0,
            unit="currency",
            interpretation_es="Costo por cada conversion/accion",
        ),
        IndustryBenchmarkEntry(
            metric_name="CPM",
            low=8.0,
            median=13.48,
            high=20.0,
            unit="currency",
            interpretation_es="Costo por cada mil impresiones",
        ),
        # ── Website / GA4 ──
        IndustryBenchmarkEntry(
            metric_name="engagementRate",
            low=45.0,
            median=56.0,
            high=70.0,
            unit="percentage",
            interpretation_es=(
                "Porcentaje de sesiones con interacción activa. "
                ">50% saludable, E-commerce 70-80%, B2B 75-85%"
            ),
        ),
        IndustryBenchmarkEntry(
            metric_name="bounceRate",
            low=25.0,
            median=40.0,
            high=55.0,
            unit="percentage",
            interpretation_es=(
                "Porcentaje de sesiones sin interacción. "
                "<40% bueno, >55% revisar contenido y velocidad"
            ),
        ),
        IndustryBenchmarkEntry(
            metric_name="averageSessionDuration",
            low=60.0,
            median=137.0,
            high=300.0,
            unit="seconds",
            interpretation_es=(
                "Duración promedio de sesión. <30s sin valor, >180s alto engagement"
            ),
        ),
        # ── Instagram Organic ──
        IndustryBenchmarkEntry(
            metric_name="ig_engagement_rate",
            low=0.30,
            median=0.50,
            high=1.20,
            unit="percentage",
            interpretation_es=(
                "Tasa de engagement orgánico IG. >0.5% promedio global, >1.2% top 25%"
            ),
        ),
        IndustryBenchmarkEntry(
            metric_name="ig_saves_rate",
            low=0.5,
            median=1.2,
            high=2.5,
            unit="percentage",
            interpretation_es=(
                "Tasa de guardados sobre vistas. Alto = contenido educativo valioso"
            ),
        ),
        # ── YouTube Organic ──
        IndustryBenchmarkEntry(
            metric_name="avg_view_percentage",
            low=30.0,
            median=50.0,
            high=70.0,
            unit="percentage",
            interpretation_es=(
                "Porcentaje promedio de retención de video. Mide calidad del contenido."
            ),
        ),
        IndustryBenchmarkEntry(
            metric_name="card_click_rate",
            low=1.0,
            median=3.0,
            high=7.0,
            unit="percentage",
            interpretation_es=(
                "Efectividad de las tarjetas informativas dentro del video."
            ),
        ),
        IndustryBenchmarkEntry(
            metric_name="end_screen_click_rate",
            low=0.5,
            median=2.0,
            high=5.0,
            unit="percentage",
            interpretation_es="Efectividad de los elementos de pantalla final.",
        ),
        # ── Email Marketing ──
        IndustryBenchmarkEntry(
            metric_name="open_rate",
            low=10.0,
            median=18.0,
            high=40.0,
            unit="percentage",
            interpretation_es=(
                "Tasa de apertura de emails. 18% promedio global. >40% excelente."
            ),
        ),
        IndustryBenchmarkEntry(
            metric_name="click_rate",
            low=1.0,
            median=2.6,
            high=4.0,
            unit="percentage",
            interpretation_es="Tasa de clics sobre emails enviados.",
        ),
        IndustryBenchmarkEntry(
            metric_name="click_to_open_rate",
            low=8.0,
            median=14.1,
            high=20.0,
            unit="percentage",
            interpretation_es=("Calidad del contenido post-apertura. >15% bueno."),
        ),
        IndustryBenchmarkEntry(
            metric_name="bounce_rate",
            low=0.0,
            median=0.7,
            high=5.0,
            unit="percentage",
            interpretation_es="Tasa de rebote. >5% indica lista sucia.",
        ),
        IndustryBenchmarkEntry(
            metric_name="unsubscribe_rate",
            low=0.0,
            median=0.1,
            high=0.5,
            unit="percentage",
            interpretation_es=(
                "Tasa de desuscripción. >0.5% indica contenido desalineado."
            ),
        ),
        IndustryBenchmarkEntry(
            metric_name="completion_rate",
            low=30.0,
            median=45.0,
            high=60.0,
            unit="percentage",
            interpretation_es=(
                "Tasa de completado de automatizaciones. Mide eficacia de secuencias."
            ),
        ),
    ],
    IndustryCategory.EDUCATION: [
        IndustryBenchmarkEntry(
            metric_name="CPL",
            low=5.0,
            median=7.85,
            high=12.0,
            unit="currency",
            interpretation_es="Costo por cada lead generado",
        ),
        IndustryBenchmarkEntry(
            metric_name="conversion_rate",
            low=6.0,
            median=10.0,
            high=15.0,
            unit="percentage",
            interpretation_es=("Tasa de conversion tipica para educacion online"),
        ),
    ],
    IndustryCategory.FITNESS: [
        IndustryBenchmarkEntry(
            metric_name="conversion_rate",
            low=8.0,
            median=14.29,
            high=20.0,
            unit="percentage",
            interpretation_es=("Tasa de conversion tipica para educacion online"),
        ),
    ],
    IndustryCategory.ECOMMERCE: [
        IndustryBenchmarkEntry(
            metric_name="CPA",
            low=25.0,
            median=35.0,
            high=55.0,
            unit="currency",
            interpretation_es="Costo por cada conversion/accion",
        ),
        IndustryBenchmarkEntry(
            metric_name="ROAS",
            low=2.0,
            median=3.0,
            high=5.0,
            unit="ratio",
            interpretation_es="Retorno por cada dolar invertido en ads",
        ),
    ],
    IndustryCategory.SAAS: [
        IndustryBenchmarkEntry(
            metric_name="CPL",
            low=30.0,
            median=50.0,
            high=80.0,
            unit="currency",
            interpretation_es="Costo por cada lead generado",
        ),
        IndustryBenchmarkEntry(
            metric_name="CPA",
            low=50.0,
            median=80.0,
            high=120.0,
            unit="currency",
            interpretation_es="Costo por cada conversion/accion",
        ),
    ],
    IndustryCategory.BEAUTY: [
        IndustryBenchmarkEntry(
            metric_name="CPL",
            low=10.0,
            median=20.0,
            high=35.0,
            unit="currency",
            interpretation_es="Costo por cada lead generado",
        ),
        IndustryBenchmarkEntry(
            metric_name="CPA",
            low=15.0,
            median=30.0,
            high=50.0,
            unit="currency",
            interpretation_es="Costo por cada conversion/accion",
        ),
    ],
    IndustryCategory.SERVICES: [
        IndustryBenchmarkEntry(
            metric_name="CPL",
            low=20.0,
            median=35.0,
            high=55.0,
            unit="currency",
            interpretation_es="Costo por cada lead generado",
        ),
        IndustryBenchmarkEntry(
            metric_name="CPA",
            low=30.0,
            median=50.0,
            high=75.0,
            unit="currency",
            interpretation_es="Costo por cada conversion/accion",
        ),
    ],
}


# ---------------------------------------------------------------------------
# Free-text to IndustryCategory mapping
# ---------------------------------------------------------------------------

INDUSTRY_ALIASES: dict[str, IndustryCategory] = {
    # EDUCATION
    "educacion": IndustryCategory.EDUCATION,
    "educación": IndustryCategory.EDUCATION,
    "cursos": IndustryCategory.EDUCATION,
    "formación": IndustryCategory.EDUCATION,
    "coaching": IndustryCategory.EDUCATION,
    # ECOMMERCE
    "tienda": IndustryCategory.ECOMMERCE,
    "ecommerce": IndustryCategory.ECOMMERCE,
    "e-commerce": IndustryCategory.ECOMMERCE,
    "shop": IndustryCategory.ECOMMERCE,
    "retail": IndustryCategory.ECOMMERCE,
    "comercio": IndustryCategory.ECOMMERCE,
    # SERVICES
    "servicios": IndustryCategory.SERVICES,
    "consultoría": IndustryCategory.SERVICES,
    "consultoria": IndustryCategory.SERVICES,
    "agencia": IndustryCategory.SERVICES,
    # FITNESS
    "fitness": IndustryCategory.FITNESS,
    "gym": IndustryCategory.FITNESS,
    "gimnasio": IndustryCategory.FITNESS,
    "salud": IndustryCategory.FITNESS,
    "bienestar": IndustryCategory.FITNESS,
    "wellness": IndustryCategory.FITNESS,
    # SAAS
    "saas": IndustryCategory.SAAS,
    "software": IndustryCategory.SAAS,
    "plataforma": IndustryCategory.SAAS,
    "app": IndustryCategory.SAAS,
    # BEAUTY
    "belleza": IndustryCategory.BEAUTY,
    "beauty": IndustryCategory.BEAUTY,
    "cosmética": IndustryCategory.BEAUTY,
    "cosmetica": IndustryCategory.BEAUTY,
    "moda": IndustryCategory.BEAUTY,
    "fashion": IndustryCategory.BEAUTY,
}


# ---------------------------------------------------------------------------
# Frequency fatigue threshold
# ---------------------------------------------------------------------------

FREQUENCY_FATIGUE_THRESHOLD: float = 3.0


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def normalize_industry(free_text: str | None) -> IndustryCategory:
    """Resolve free-text industry description to an ``IndustryCategory``.

    Resolution order:
    1. Exact match (case-insensitive) against ``INDUSTRY_ALIASES``.
    2. Substring match (any alias contained in the text).
    3. Fallback to ``GENERAL``.
    """
    if not free_text:
        return IndustryCategory.GENERAL

    normalized = free_text.strip().lower()
    if not normalized:
        return IndustryCategory.GENERAL

    # Exact match
    if normalized in INDUSTRY_ALIASES:
        return INDUSTRY_ALIASES[normalized]

    # Substring match — check if any alias appears within the text
    for alias, category in INDUSTRY_ALIASES.items():
        if alias in normalized:
            return category

    return IndustryCategory.GENERAL


def get_benchmarks(
    industry: IndustryCategory,
    metric_name: str,
) -> IndustryBenchmarkEntry | None:
    """Look up benchmark data for a metric within an industry.

    Checks industry-specific benchmarks first, then falls back to GENERAL.
    Returns ``None`` when no benchmark data exists for the metric.
    """
    # Industry-specific lookup
    for entry in INDUSTRY_BENCHMARKS.get(industry, []):
        if entry.metric_name == metric_name:
            return entry

    # Fallback to GENERAL (skip if already looking at GENERAL)
    if industry is not IndustryCategory.GENERAL:
        for entry in INDUSTRY_BENCHMARKS.get(IndustryCategory.GENERAL, []):
            if entry.metric_name == metric_name:
                return entry

    return None
