"""``web_research`` — generic public-web search (wraps TavilySearchService).

Previously lived under ``tools/interview/``; promoted to ``shared_tools``
on 2026-04-22 so it's available in chat mode as well as guided mode —
useful for "busca precios de coaching en Perú" type questions from any
route.
"""

from __future__ import annotations

import json

import structlog
from langchain_core.tools import tool

from src.modules.copilot.infrastructure.web.tavily_search import TavilySearchService

logger = structlog.get_logger()


@tool
async def web_research(query: str, max_results: int = 5) -> str:
    """Realiza una búsqueda en la web pública y devuelve los mejores resultados.

    Úsalo cuando el usuario pida referencias de mercado, precios, ejemplos
    de la competencia, o cualquier dato que no esté en los módulos de
    Nicolify. Evita llamarlo para información que ya esté en el tenant
    (para eso usa ``search_knowledge_base`` o tools de módulo).

    Args:
        query: Texto a buscar. Sé específico, incluye país/región si aplica.
        max_results: Máximo de resultados a devolver (default 5).

    Returns:
        JSON con una lista ``results`` de ``{title, url, content, relevance}``.

    """
    service = TavilySearchService()
    try:
        results = await service.search(query=query, max_results=max_results)
    except Exception as exc:  # noqa: BLE001 — tool resilience
        logger.warning("web_research_failed", query=query, error=str(exc))
        return json.dumps({"results": [], "error": str(exc)})

    return json.dumps(
        {
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.content_snippet,
                    "relevance": r.relevance_score,
                }
                for r in results
            ],
        },
    )
