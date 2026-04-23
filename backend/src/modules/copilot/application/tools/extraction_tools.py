"""Conversational extraction tool — ingest a URL into Brand or Offer Studio.

Replaces the former "extract" button inside the Brand/Offer wizards by
exposing a single LangChain tool the Copilot can call when the user says
things like:

    "extrae todo de https://visionarias.lat hacia mi brand studio"
    "completa los campos vacíos del brand desde ese link"
    "analiza esta URL y actualiza mi oferta actual"

No new extraction infrastructure is introduced. The tool is a thin adapter
that:

1. Validates inputs (module, url, scope, mode).
2. Dispatches the appropriate ARQ worker (``run_brand_extraction`` or
   ``run_offer_extraction``) reusing the pipelines the REST endpoints drive.
3. Returns a structured JSON payload with the ``job_id`` and the Redis poll
   endpoint the frontend already knows how to query.

The tool does NOT decide scope. When the user intent is ambiguous - "extrae
de esta web" could mean "new brand from scratch", "complete missing fields",
or "just this section" - the LLM MUST call ``clarify`` first with 2-3 quick
options, then call this tool with the resolved ``scope`` and ``mode``.

Tenant isolation: tenant_id is read from ``get_tenant_id()`` (request-scoped
ContextVar), never taken as a tool argument.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

import structlog
from langchain_core.tools import tool

from src.core.arq_pool import get_arq_pool
from src.core.context import get_tenant_id
from src.core.database import redis_client

logger = structlog.get_logger()


_URL_RE = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)


def _err(message: str, **extra: object) -> str:
    """Shape an error payload in the same envelope as success.

    The LLM pattern-matches on ``status`` so success and failure must share
    the same top-level structure.
    """
    return json.dumps({"status": "error", "message": message, **extra})


def _validate_extract_args(  # noqa: PLR0911 — independent guard clauses read cleaner as flat early-returns than a collected list.
    module: str,
    url: str,
    scope: str,
    offer_id: str | None,
) -> str | None:
    """Return a JSON error payload if any guard fails, else ``None``."""
    if get_tenant_id() is None:
        return _err("No hay contexto de tenant. Vuelve a iniciar sesión.")
    if not url or not url.strip():
        return _err("Falta la URL a analizar.")
    if not _URL_RE.match(url.strip()):
        return _err(
            "La URL debe empezar con http:// o https:// y ser accesible públicamente.",
            url=url,
        )
    if module == "offer" and scope == "visuals":
        return _err(
            "El scope 'visuals' solo aplica a Brand Studio. Para Offer Studio usa scope='full'.",
        )
    if module == "offer":
        if not offer_id:
            return _err(
                "Falta offer_id. Usa get_module_data para identificar la oferta "
                "a actualizar antes de llamar a extract_from_url.",
            )
        try:
            UUID(offer_id)
        except ValueError:
            return _err(f"offer_id '{offer_id}' no es un UUID válido.")
    if get_arq_pool() is None:
        return _err(
            "El servicio de análisis en segundo plano no está disponible en este "
            "momento. Intenta de nuevo en unos segundos.",
        )
    if redis_client is None:
        return _err(
            "No se puede registrar el progreso del análisis. Intenta de nuevo.",
        )
    return None


async def _extract_from_url_impl(
    module: Literal["brand", "offer"],
    url: str,
    scope: Literal["full", "visuals"] = "full",
    mode: Literal["initial", "update"] = "initial",
    update_instructions: str | None = None,
    offer_id: str | None = None,
) -> str:
    """Core implementation for ``extract_from_url``.

    Kept separate from the LangChain-decorated entry point so unit tests can
    import both sides cleanly if needed.
    """
    guard_error = _validate_extract_args(module, url, scope, offer_id)
    if guard_error is not None:
        return guard_error

    tenant_id = get_tenant_id()
    arq_pool = get_arq_pool()
    # Both are guaranteed non-None by _validate_extract_args.
    assert tenant_id is not None  # noqa: S101 — narrowing for type checker
    assert arq_pool is not None  # noqa: S101 — narrowing for type checker
    assert redis_client is not None  # noqa: S101 — narrowing for type checker

    # --- Dispatch ---
    job_id = str(uuid4())
    tenant_str = str(tenant_id)
    started_at = datetime.now(UTC).isoformat()

    if module == "brand":
        progress_key = f"brand_extract:{tenant_str}:{job_id}"
        poll_endpoint = f"/api/v1/brand/extract-full-brand/status/{job_id}"
        include_visuals = scope == "visuals"

        redis_client.setex(
            progress_key,
            3600,
            json.dumps(
                {
                    "status": "queued",
                    "progress": 0,
                    "stage": "Iniciando análisis...",
                    "started_at": started_at,
                },
            ),
        )

        await arq_pool.enqueue_job(
            "run_brand_extraction",
            job_id=job_id,
            tenant_id=tenant_str,
            url=url,
            text=None,
            mode=mode,
            update_instructions=update_instructions,
            include_visuals=include_visuals,
            include_assets=False,
            dry_run=False,
        )
        logger.info(
            "copilot_extract_from_url_dispatched",
            module="brand",
            tenant_id=tenant_str,
            job_id=job_id,
            scope=scope,
            mode=mode,
            has_instructions=bool(update_instructions),
        )
    else:  # offer
        progress_key = f"offer_extract:{tenant_str}:{job_id}"
        poll_endpoint = f"/api/v1/offer/extract-full-offer/status/{job_id}"

        redis_client.setex(
            progress_key,
            3600,
            json.dumps(
                {
                    "status": "queued",
                    "progress": 0,
                    "stage": "Iniciando análisis de oferta...",
                    "started_at": started_at,
                },
            ),
        )

        await arq_pool.enqueue_job(
            "run_offer_extraction",
            job_id=job_id,
            tenant_id=tenant_str,
            offer_id=offer_id,
            url=url,
            text=None,
            mode=mode,
            update_instructions=update_instructions,
        )
        logger.info(
            "copilot_extract_from_url_dispatched",
            module="offer",
            tenant_id=tenant_str,
            offer_id=offer_id,
            job_id=job_id,
            mode=mode,
        )

    friendly = (
        "Inicié el análisis. Tarda entre 1 y 2 minutos. "
        "Te aviso cuando termine o puedes seguir conversando mientras tanto."
    )
    return json.dumps(
        {
            "status": "dispatched",
            "module": module,
            "scope": scope,
            "mode": mode,
            "job_id": job_id,
            "poll_endpoint": poll_endpoint,
            "message": friendly,
        },
    )


@tool
async def extract_from_url(
    module: Literal["brand", "offer"],
    url: str,
    scope: Literal["full", "visuals"] = "full",
    mode: Literal["initial", "update"] = "initial",
    update_instructions: str | None = None,
    offer_id: str | None = None,
) -> str:
    """Extrae datos de una URL pública hacia Brand Studio u Offer Studio.

    Antes de llamar esta tool: si el usuario no especificó el alcance, llama
    primero a ``clarify`` con opciones como
    ``["Empezar desde cero (reemplaza lo existente)",
       "Solo completar faltantes (update)",
       "Solo la sección actual"]`` para dejar claro el `scope`+`mode`.

    Args:
        module: "brand" para Brand Studio, "offer" para Offer Studio.
        url: URL pública (http/https) a analizar.
        scope: "full" extracción completa; "visuals" (solo brand) identidad
            visual rápida.
        mode: "initial" sobrescribe, "update" respeta datos existentes y
            completa faltantes.
        update_instructions: Texto libre en español dando pistas al
            extractor cuando mode="update" (ej. "solo la sección de marca").
        offer_id: UUID de la oferta a actualizar. Obligatorio si module="offer".

    Returns:
        JSON con ``status`` ("dispatched" o "error"), ``job_id``, y
        ``poll_endpoint`` para que el frontend consulte el progreso.

    """
    return await _extract_from_url_impl(
        module=module,
        url=url,
        scope=scope,
        mode=mode,
        update_instructions=update_instructions,
        offer_id=offer_id,
    )


EXTRACTION_TOOLS = [extract_from_url]

__all__ = ["EXTRACTION_TOOLS", "extract_from_url"]
