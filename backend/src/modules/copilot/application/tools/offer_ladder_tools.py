"""
Offer Ladder analysis tools — deterministic gap analysis for the copilot.

Analyzes the tenant's current offer ladder (5 value levels) and identifies
gaps, suggesting what to create next with priorities and archetypes.
"""

import structlog
from langchain_core.tools import tool
from sqlalchemy import text

from src.core.context import get_tenant_id
from src.core.database import SessionLocal

logger = structlog.get_logger()

GROUP_LABELS = {
    "lead_magnet": "Lead Magnet",
    "activacion": "Activacion",
    "transformacion": "Transformacion",
    "maximizacion": "Maximizacion",
    "corporativo": "Corporativo",
}

GAP_PRIORITIES = {
    "lead_magnet": "critico",
    "activacion": "recomendado",
    "transformacion": "critico",
    "maximizacion": "opcional",
    "corporativo": "opcional",
}

DEFAULT_SUGGESTIONS = {
    "lead_magnet": {
        "archetype": "producto",
        "preset": "producto_ebook",
        "name_hint": "Guia Gratuita",
        "price_range": "Gratis",
    },
    "activacion": {
        "archetype": "programa",
        "preset": "programa_masterclass",
        "name_hint": "Masterclass",
        "price_range": "$47-$197",
    },
    "transformacion": {
        "archetype": "programa",
        "preset": "programa_bootcamp",
        "name_hint": "Programa Principal",
        "price_range": "$497-$2,500",
    },
    "maximizacion": {
        "archetype": "servicio",
        "preset": "servicio_mentoria",
        "name_hint": "Mentoria Premium",
        "price_range": "$3,000-$10,000",
    },
    "corporativo": {
        "archetype": "servicio",
        "preset": "servicio_dfy",
        "name_hint": "Servicio Corporativo",
        "price_range": "$5,000+",
    },
}

LEVEL_ORDER = [
    "lead_magnet",
    "activacion",
    "transformacion",
    "maximizacion",
    "corporativo",
]

GAP_REASONING = {
    "lead_magnet": (
        "Sin lead magnet no hay entrada al embudo. Es lo primero que un prospecto descarga a cambio de su contacto."
    ),
    "activacion": (
        "Una oferta de activacion convierte leads frios en compradores. "
        "Es el primer intercambio monetario y genera confianza."
    ),
    "transformacion": (
        "La oferta de transformacion es el motor del negocio. Sin ella, "
        "no hay producto insignia que genere ingresos sostenibles."
    ),
    "maximizacion": (
        "Una oferta de maximizacion captura el valor de los clientes mas "
        "comprometidos que quieren atencion personalizada."
    ),
    "corporativo": (
        "Una oferta corporativa o done-for-you abre un canal de alto ticket con empresas o clientes premium."
    ),
}


def _fetch_brand_context(db, tenant_id: str) -> dict | None:
    """Fetch brand info for contextual suggestions."""
    try:
        row = (
            db.execute(
                text(
                    "SELECT niche, industry, target_audience "
                    "FROM brands WHERE tenant_id = :tid AND is_active = true "
                    "LIMIT 1",
                ),
                {"tid": tenant_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None
    except Exception as e:  # noqa: BLE001 — tool execution resilience
        logger.warning(
            "offer_ladder_brand_fetch_error",
            tenant_id=tenant_id,
            error=str(e),
        )
        return None


def _fetch_offers(db, tenant_id: str) -> list[dict]:
    """Fetch active offers grouped by value level."""
    try:
        rows = (
            db.execute(
                text(
                    "SELECT id, name, archetype, format_hint, offer_value_level, "
                    "delivery_model, status "
                    "FROM products WHERE tenant_id = :tid AND is_active = true "
                    "ORDER BY created_at",
                ),
                {"tid": tenant_id},
            )
            .mappings()
            .all()
        )
        return [dict(r) for r in rows]
    except Exception as e:  # noqa: BLE001 — tool execution resilience
        logger.warning("offer_ladder_fetch_error", tenant_id=tenant_id, error=str(e))
        return []


def _group_by_level(offers: list[dict]) -> dict[str, list[dict]]:
    """Group offers by their offer_value_level."""
    groups: dict[str, list[dict]] = {level: [] for level in LEVEL_ORDER}
    for offer in offers:
        level = offer.get("offer_value_level")
        if level and level in groups:
            groups[level].append(offer)
    return groups


def _build_current_status(groups: dict[str, list[dict]]) -> str:
    """Build markdown for current ladder status."""
    lines = ["## Estado Actual del Offer Ladder\n"]
    for level in LEVEL_ORDER:
        label = GROUP_LABELS[level]
        offers_in_group = groups[level]
        if offers_in_group:
            names = ", ".join(o.get("name", "Sin nombre") for o in offers_in_group)
            lines.append(f"- **{label}**: {len(offers_in_group)} oferta(s) — {names}")
        else:
            lines.append(f"- **{label}**: _Vacio_")
    return "\n".join(lines)


def _build_gap_analysis(groups: dict[str, list[dict]], brand: dict | None) -> str:
    """Build markdown for gap analysis with suggestions."""
    gaps = [level for level in LEVEL_ORDER if not groups[level]]

    if not gaps:
        return "\n## Analisis de Gaps\n\nNo hay gaps. Tu offer ladder esta completo."

    lines = ["\n## Analisis de Gaps\n"]

    for level in gaps:
        label = GROUP_LABELS[level]
        priority = GAP_PRIORITIES[level]
        suggestion = DEFAULT_SUGGESTIONS[level]
        reasoning = GAP_REASONING[level]

        priority_badge = {
            "critico": "CRITICO",
            "recomendado": "RECOMENDADO",
            "opcional": "OPCIONAL",
        }.get(priority, priority.upper())

        lines.append(f"### {label} [{priority_badge}]\n")
        lines.append(f"**Por que:** {reasoning}\n")
        lines.append(f"- Archetype sugerido: `{suggestion['archetype']}`")
        lines.append(f"- Preset: `{suggestion['preset']}`")
        lines.append(f"- Nombre sugerido: {suggestion['name_hint']}")
        lines.append(f"- Rango de precio: {suggestion['price_range']}")

        if brand:
            niche = brand.get("niche")
            if niche:
                lines.append(f"- Contexto de nicho: {niche}")

        lines.append("")

    return "\n".join(lines)


def _calculate_completeness(groups: dict[str, list[dict]]) -> str:
    """Calculate and format completeness score."""
    filled = sum(1 for level in LEVEL_ORDER if groups[level])
    total = len(LEVEL_ORDER)
    pct = int((filled / total) * 100)

    lines = [f"\n## Completitud: {filled}/{total} ({pct}%)\n"]

    if pct == 100:
        lines.append(
            "Tu offer ladder esta completo. Revisa cada oferta para asegurar que los detalles esten bien configurados.",
        )
    elif pct >= 60:
        lines.append(
            "Buen avance. Completa los niveles faltantes para maximizar el valor de cada cliente en tu embudo.",
        )
    else:
        lines.append(
            "Tu offer ladder necesita mas ofertas. Empieza por los gaps marcados como CRITICO.",
        )

    return "\n".join(lines)


@tool
def analyze_offer_ladder() -> str:
    """Analyze the current offer ladder and identify gaps.

    Examines the tenant's offers across the 5 value levels (lead_magnet,
    activacion, transformacion, maximizacion, corporativo), identifies
    missing levels, and suggests what to create next with priorities.

    Returns:
        Structured markdown with current status, gap analysis, and completeness score.
    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return "Error: No se pudo determinar el tenant. Asegurate de estar autenticado."

    tid = str(tenant_id)
    db = SessionLocal()
    try:
        brand = _fetch_brand_context(db, tid)
        offers = _fetch_offers(db, tid)
        groups = _group_by_level(offers)

        parts = [
            _build_current_status(groups),
            _build_gap_analysis(groups, brand),
            _calculate_completeness(groups),
        ]

        logger.info(
            "offer_ladder_analyzed",
            tenant_id=tid,
            total_offers=len(offers),
            filled_levels=sum(1 for level in LEVEL_ORDER if groups[level]),
        )

        return "\n".join(parts)
    finally:
        db.close()


OFFER_LADDER_TOOLS = [analyze_offer_ladder]
