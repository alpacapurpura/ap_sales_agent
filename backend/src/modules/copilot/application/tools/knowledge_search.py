"""``knowledge_search`` — transversal tool for the curated marketing KB.

Replaces the legacy ``search_knowledge_base(query, scope)`` tool. The new
signature drops ``scope`` (corpus is now globally curated, no per-tenant
business/help split) and adds optional ``domain`` / ``methodology``
filters.

Output is markdown-formatted with explicit ``methodology`` labels so the
LLM can cite the source method ("aplicando Hormozi value equation:…")
when synthesising the user-facing answer.

[COPILOT-MARKETING-KB-F10]
"""

from __future__ import annotations

import structlog
from langchain_core.tools import tool

from src.modules.copilot.infrastructure.qdrant.marketing_kb_store import (
    ALLOWED_DOMAINS,
    ALLOWED_METHODOLOGIES,
    MarketingKbStore,
)

logger = structlog.get_logger()

_METHODOLOGY_LABEL_ES: dict[str, str] = {
    "nicolify_owned": "Metodología Nicolify",
    "storybrand": "StoryBrand",
    "hormozi": "Hormozi",
    "cialdini": "Cialdini",
    "aida": "AIDA",
    "pas": "PAS",
    "jtbd": "Jobs-to-be-Done",
    "fab": "FAB",
    "4u": "4U Headlines",
}


def _format_chunk(item: dict) -> str:
    method = item.get("methodology") or "general"
    method_label = _METHODOLOGY_LABEL_ES.get(method, method)
    domain = item.get("domain") or "general"
    breadcrumb = " > ".join(item.get("breadcrumb") or []) or "—"
    score = item.get("score") or 0.0
    content = (item.get("content") or "").strip()
    return (
        f"**Método:** {method_label} · **Dominio:** {domain} · "
        f"**Sección:** {breadcrumb} · **Score:** {score:.2f}\n\n{content}"
    )


def _resolve_store(_store: MarketingKbStore | None) -> MarketingKbStore:
    return _store if _store is not None else MarketingKbStore()


def knowledge_search_impl(
    query: str,
    *,
    domain: str | None = None,
    methodology: str | None = None,
    limit: int = 5,
    store: MarketingKbStore | None = None,
) -> str:
    """Pure function used by the tool wrapper and tests."""
    if not query.strip():
        return "Pregunta vacía. Indica qué framework o tema necesitas."

    if domain is not None and domain not in ALLOWED_DOMAINS:
        return f"Dominio inválido: {domain!r}. Opciones: {sorted(ALLOWED_DOMAINS)}."
    if methodology is not None and methodology not in ALLOWED_METHODOLOGIES:
        return f"Metodología inválida: {methodology!r}. Opciones: {sorted(ALLOWED_METHODOLOGIES)}."

    capped = max(1, min(limit, 10))

    try:
        results = _resolve_store(store).search(
            query,
            domain=domain,
            methodology=methodology,
            limit=capped,
        )
    except Exception as exc:
        logger.exception("knowledge_search_error", error=str(exc))
        return "No pude consultar la base de conocimiento. Intenta de nuevo."

    if not results:
        return "No encontré material curado para esa consulta. Reformula con otro framework o término más amplio."

    lines = ["## Material curado relevante\n"]
    for idx, item in enumerate(results, start=1):
        lines.append(f"### Resultado {idx}\n")
        lines.append(_format_chunk(item))
        lines.append("")
    lines.append(
        "Cita el método aplicado al responder al usuario (ejemplo: 'aplicando Hormozi value equation: …').",
    )
    return "\n".join(lines).rstrip() + "\n"


@tool
def knowledge_search(
    query: str,
    domain: str | None = None,
    methodology: str | None = None,
    limit: int = 5,
) -> str:
    """Busca material curado de marketing/ventas en la base de conocimiento global.

    Úsalo SIEMPRE antes de responder cuando el usuario pregunte por un
    framework (StoryBrand, Hormozi, Cialdini, AIDA, PAS, JTBD, FAB, 4U) o
    un concepto avanzado (grand slam offer, value equation, principios
    de influencia, narrativa, manejo de objeciones).

    Args:
        query: Pregunta o tema a buscar en lenguaje natural.
        domain: Filtro opcional (brand | offer | copy | objections |
            pricing | funnel | audience).
        methodology: Filtro opcional (nicolify_owned | storybrand |
            hormozi | cialdini | aida | pas | jtbd | fab | 4u).
        limit: Máximo de resultados (1..10, default 5).

    Returns:
        Markdown con chunks relevantes, cada uno etiquetado con método
        y dominio para que cites el origen al responder.

    """
    return knowledge_search_impl(
        query,
        domain=domain,
        methodology=methodology,
        limit=limit,
    )


KNOWLEDGE_SEARCH_TOOLS = [knowledge_search]
