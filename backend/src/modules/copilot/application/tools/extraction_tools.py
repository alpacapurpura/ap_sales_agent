"""Conversational extraction tools — ingest a URL or document into Brand/Offer/Asset/Persona Studio.

Replaces the former "extract" button inside the Brand/Offer wizards by
exposing LangChain tools the Copilot can call when the user says things like:

    "extrae todo de https://visionarias.lat hacia mi brand studio"
    "completa los campos vacíos del brand desde ese link"
    "analiza esta URL y actualiza mi oferta actual"
    "extrae del documento que subí"

No new extraction infrastructure is introduced. The tools are thin adapters
that:

1. Validate inputs (module, url/asset_id, scope, mode).
2. Dispatch the appropriate ARQ worker (``run_brand_extraction`` or
   ``run_offer_extraction``) reusing the pipelines the REST endpoints drive.
3. Return a structured JSON payload with the ``job_id`` and the Redis poll
   endpoint the frontend already knows how to query.

The tools do NOT decide scope. When the user intent is ambiguous — "extrae
de esta web" could mean "new brand from scratch", "complete missing fields",
or "just this section" — the LLM MUST call ``clarify`` first with 2-3 quick
options, then call this tool with the resolved ``scope`` and ``mode``.

### Scope clarification protocol (Phase 0 — LLM instruction)

Before calling ``extract_from_url`` or ``extract_from_doc``:

1. Si el usuario NO especificó el alcance, emite una card ``clarify`` con
   dos ejes:
     - fieldPath: "__scope__"
       issue: "¿Qué quieres extraer?"
       options:
         - "Solo {current_section_label} (esta página)"  ← si ruta = /brand-studio/{section}
         - "Todo Brand Studio"                           ← módulo completo
         - "Solo una sección específica…"                ← permite elegir

     - fieldPath: "__mode__"
       issue: "¿Cómo escribo los campos?"
       options:
         - "Solo llenar vacíos"        → mode="update"
         - "Reemplazar todo"           → mode="initial"
         - "Sugerir (no escribir)"     → mode="suggest"

2. Usa ``ClientContext.current_route`` para inferir ``{current_section_label}``:
   - ``/brand-studio/identity`` → "Identidad"
   - ``/brand-studio/strategy`` → "Estrategia"
   - ``/brand-studio/positioning`` → "Posicionamiento"
   - ``/brand-studio/narrative`` → "Narrativa"
   - ``/brand-studio/audience`` → "Audiencia"
   - ``/brand-studio/visuals`` → "Visuales"
   - ``/brand-studio/communication-assets`` → "Activos de Comunicación"
   - ``/brand-studio/authority`` → "Autoridad"
   - ``/brand-studio/story`` → "Historia"
   - ``/brand-studio/people-contact`` → "Equipo y Contacto"
   - ``/offer-studio/.../{section}`` → misma lógica para offer sections

3. Tras la respuesta del usuario:
   - "Solo [sección actual]" → scope="section", section=<slug de la ruta>
   - "Todo [módulo]" → scope="full"
   - "Solo llenar vacíos" → mode="update"
   - "Reemplazar todo" → mode="initial"
   - "Sugerir (no escribir)" → mode="suggest"

### Few-shot example

Usuario en ``/brand-studio/identity``: "analiza visionarias.pe"

LLM → llama a ``clarify`` con:
  clarify_items: [
    { field_path: "__scope__", issue: "¿Qué quieres extraer?",
      options: ["Solo Identidad (esta página)", "Todo Brand Studio", "Solo una sección específica…"] },
    { field_path: "__mode__", issue: "¿Cómo escribo los campos?",
      options: ["Solo llenar vacíos", "Reemplazar todo", "Sugerir (no escribir)"] }
  ]

Usuario elige "Solo Identidad (esta página)" + "Solo llenar vacíos"

LLM → llama a ``extract_from_url`` con:
  module="brand", url="https://visionarias.pe",
  scope="section", section="identity", mode="update"

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
from luana_core_copilot.application.extraction.active_job_persistence import (
    write_active_job,
)
from luana_core_copilot.application.extraction.active_job_state import (
    ActiveExtractionJob,
)
from luana_core_copilot.application.guided.persistence import (
    read_state as read_guided_state,
)
from luana_core_platform.core.arq_pool import get_arq_pool
from luana_core_platform.core.context import get_conversation_id, get_tenant_id, get_user_id
from luana_core_platform.core.database import redis_client
from luana_core_platform.domain.extraction_jobs import ExtractionJob

logger = structlog.get_logger()


def _record_active_extraction_job(
    *,
    conversation_id: str | None,
    tenant_id: UUID | None,
    job_id: str,
    module: str,
    entity_id: str | None,
    source_kind: str,
    source_ref: str,
    scope: str,
    mode: str,
    started_at: str,
) -> None:
    """Persist the in-flight extraction in ``procedure_state.active_extraction_job``.

    Called after a successful ARQ dispatch so the next copilot turn sees the
    job as active. ``paused_at_block`` is copied from the guided state when
    present — the prompt layer uses it to resume guided questions on the
    same block once the worker finishes.

    Best-effort: write failures log and return without raising — a persistence
    glitch must never revert a successful dispatch.
    """
    if not conversation_id or tenant_id is None:
        return
    try:
        guided = read_guided_state(conversation_id, tenant_id)
    except Exception:  # noqa: BLE001 — best-effort persistence
        guided = None
    paused_at_block = guided.current_block_id if guided is not None else None
    job_state = ActiveExtractionJob(
        job_id=job_id,
        module=module,
        entity_id=entity_id,
        source_kind=source_kind,
        source_ref=source_ref,
        scope=scope,
        mode=mode,
        paused_at_block=paused_at_block,
        started_at=started_at,
    )
    try:
        write_active_job(conversation_id, job_state, tenant_id)
    except Exception:  # noqa: BLE001 — best-effort persistence
        logger.warning(
            "active_extraction_job_write_failed",
            job_id=job_id,
            module=module,
            conversation_id=conversation_id,
        )


_URL_RE = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)

# Human-readable module labels (Spanish LatAm neutro)
_MODULE_LABELS: dict[str, str] = {
    "brand": "Brand Studio",
    "offer": "Offer Studio",
    "asset": "Assets",
    "persona": "Buyer Persona",
}

# Human-readable section labels for brand sections
_BRAND_SECTION_LABELS: dict[str, str] = {
    "identity": "Identidad",
    "strategy": "Estrategia",
    "positioning": "Posicionamiento",
    "narrative": "Narrativa",
    "audience": "Audiencia",
    "visuals": "Visuales",
    "communication-assets": "Activos de Comunicación",
    "communication_assets": "Activos de Comunicación",
    "authority": "Autoridad",
    "story": "Historia",
    "people-contact": "Equipo y Contacto",
    "people_contact": "Equipo y Contacto",
}

# Human-readable section labels for offer sections
_OFFER_SECTION_LABELS: dict[str, str] = {
    "promise": "Promesa",
    "details": "Detalles",
    "strategy": "Estrategia",
    "psychology": "Psicología",
    "value-stack": "Stack de Valor",
    "value_stack": "Stack de Valor",
    "closing": "Cierre",
}


def _compose_target_label(
    module: str,
    scope: str,
    section: str | None,
) -> str:
    """Build a user-facing label for the extraction target (Spanish LatAm neutro).

    Examples:
    - module="brand", scope="full" → "Brand Studio"
    - module="brand", scope="section", section="identity" → "Brand Studio · Identidad"
    - module="offer", scope="full" → "Offer Studio"
    """
    module_label = _MODULE_LABELS.get(module, module.replace("_", " ").title())
    if scope == "section" and section:
        # Try brand labels first, then offer labels
        section_label = (
            _BRAND_SECTION_LABELS.get(section)
            or _OFFER_SECTION_LABELS.get(section)
            or section.replace("-", " ").replace("_", " ").title()
        )
        return f"{module_label} · {section_label}"
    if scope == "field" and section:
        section_label = (
            _BRAND_SECTION_LABELS.get(section)
            or _OFFER_SECTION_LABELS.get(section)
            or section.replace("-", " ").replace("_", " ").title()
        )
        return f"{module_label} · {section_label}"
    return module_label


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
    section: str | None,
    field: str | None,
    entity_id: str | None,
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
    if scope == "visuals" and module != "brand":
        return _err(
            "El scope 'visuals' solo aplica a Brand Studio. Para Offer Studio usa scope='full'.",
        )
    if scope == "section" and not section:
        return _err(
            "El scope 'section' requiere el parámetro 'section' con el slug de la sección "
            "(ej. 'identity', 'strategy'). Usa clarify para preguntar al usuario qué sección quiere.",
        )
    if scope == "field" and not field:
        return _err(
            "El scope 'field' requiere el parámetro 'field' con el path del campo "
            "(ej. 'identity.brand_name'). Usa clarify para preguntar al usuario qué campo quiere.",
        )
    if module == "offer":
        if not entity_id:
            return _err(
                "Falta entity_id (o offer_id). Usa get_module_data para identificar la oferta "
                "a actualizar antes de llamar a extract_from_url.",
            )
        try:
            UUID(entity_id)
        except ValueError:
            return _err(f"entity_id '{entity_id}' no es un UUID válido.")
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
    module: Literal["brand", "offer", "asset", "persona"],
    url: str,
    scope: Literal["full", "visuals", "section", "field"] = "full",
    mode: Literal["initial", "update", "suggest"] = "initial",
    section: str | None = None,
    field: str | None = None,
    update_instructions: str | None = None,
    entity_id: str | None = None,
) -> str:
    """Core implementation for ``extract_from_url``.

    Kept separate from the LangChain-decorated entry point so unit tests can
    import both sides cleanly if needed.

    ``entity_id`` is the canonical identifier. The caller is responsible for
    aliasing ``offer_id`` → ``entity_id`` before calling this function.
    """
    guard_error = _validate_extract_args(module, url, scope, section, field, entity_id)
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
    target_label_es = _compose_target_label(module, scope, section)

    if module == "brand":
        progress_key = f"brand_extract:{tenant_str}:{job_id}"
        poll_endpoint = f"/api/v1/brand/tools/extract-full-brand/status/{job_id}"
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
                    "filled_fields": [],
                    "filled_fields_by_section": {},
                    "sections_touched": [],
                    "sections_completed": [],
                    "newly_completed_section": None,
                },
            ),
        )

        conversation_id_val = get_conversation_id()
        user_id_val = get_user_id()
        await arq_pool.enqueue_job(
            ExtractionJob.BRAND.value,
            job_id=job_id,
            tenant_id=tenant_str,
            url=url,
            text=None,
            mode=mode,
            update_instructions=update_instructions,
            include_visuals=include_visuals,
            include_assets=False,
            dry_run=False,
            conversation_id=conversation_id_val,
            user_id=str(user_id_val) if user_id_val else None,
        )
        _record_active_extraction_job(
            conversation_id=conversation_id_val,
            tenant_id=tenant_id,
            job_id=job_id,
            module="brand",
            entity_id=None,
            source_kind="url",
            source_ref=url,
            scope=scope,
            mode=mode,
            started_at=started_at,
        )
        logger.info(
            "copilot_extract_from_url_dispatched",
            module="brand",
            tenant_id=tenant_str,
            job_id=job_id,
            scope=scope,
            section=section,
            mode=mode,
            has_instructions=bool(update_instructions),
            conversation_id=conversation_id_val,
        )
    elif module == "offer":
        progress_key = f"offer_extract:{tenant_str}:{job_id}"
        poll_endpoint = f"/api/v1/offer/tools/extract-full-offer/status/{job_id}"

        redis_client.setex(
            progress_key,
            3600,
            json.dumps(
                {
                    "status": "queued",
                    "progress": 0,
                    "stage": "Iniciando análisis de oferta...",
                    "started_at": started_at,
                    "filled_fields": [],
                    "filled_fields_by_section": {},
                    "sections_touched": [],
                    "sections_completed": [],
                    "newly_completed_section": None,
                },
            ),
        )

        conversation_id_val = get_conversation_id()
        await arq_pool.enqueue_job(
            ExtractionJob.OFFER.value,
            job_id=job_id,
            tenant_id=tenant_str,
            offer_id=entity_id,
            url=url,
            text=None,
            mode=mode,
            update_instructions=update_instructions,
            conversation_id=conversation_id_val,
        )
        _record_active_extraction_job(
            conversation_id=conversation_id_val,
            tenant_id=tenant_id,
            job_id=job_id,
            module="offer",
            entity_id=entity_id,
            source_kind="url",
            source_ref=url,
            scope=scope,
            mode=mode,
            started_at=started_at,
        )
        logger.info(
            "copilot_extract_from_url_dispatched",
            module="offer",
            tenant_id=tenant_str,
            offer_id=entity_id,
            job_id=job_id,
            scope=scope,
            mode=mode,
        )
    else:
        # asset / persona: not yet fully implemented — return error with clear message
        return _err(
            f"El módulo '{module}' aún no soporta extracción desde URL en esta versión. Disponible próximamente.",
            module=module,
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
            "section": section,
            "field": field,
            "job_id": job_id,
            "poll_endpoint": poll_endpoint,
            "target_label_es": target_label_es,
            "source_kind": "url",
            "source_ref": url,
            "eta_seconds": 90,
            "message": friendly,
        },
    )


@tool
async def extract_from_url(
    module: Literal["brand", "offer", "asset", "persona"],
    url: str,
    scope: Literal["full", "visuals", "section", "field"] = "full",
    mode: Literal["initial", "update", "suggest"] = "initial",
    section: str | None = None,
    field: str | None = None,
    update_instructions: str | None = None,
    entity_id: str | None = None,
    offer_id: str | None = None,
) -> str:
    """Extrae datos de una URL pública hacia Brand Studio, Offer Studio, Assets o Persona.

    IMPORTANTE — Antes de llamar esta tool:

    Si el usuario no especificó el alcance, llama primero a ``clarify`` con dos ejes:
      1. Alcance (fieldPath="__scope__"):
         options: ["Solo {sección actual} (esta página)", "Todo {módulo}", "Solo una sección…"]
      2. Modo (fieldPath="__mode__"):
         options: ["Solo llenar vacíos", "Reemplazar todo", "Sugerir (no escribir)"]

    Usa ``ClientContext.current_route`` para inferir la sección actual:
    - /brand-studio/identity → section="identity", label="Identidad"
    - /brand-studio/strategy → section="strategy", label="Estrategia"
    - /offer-studio/…/promise → section="promise", label="Promesa"

    Mapeo de respuesta de clarify al parámetro:
    - "Solo llenar vacíos" → mode="update"
    - "Reemplazar todo" → mode="initial"
    - "Sugerir (no escribir)" → mode="suggest"
    - "Solo [sección]" → scope="section", section=<slug>
    - "Todo [módulo]" → scope="full"

    Args:
        module: Studio destino. "brand" = Brand Studio, "offer" = Offer Studio,
            "asset" = Assets, "persona" = Buyer Persona.
        url: URL pública (http/https) a analizar.
        scope: "full" extracción completa del módulo; "visuals" (solo brand)
            identidad visual rápida; "section" extrae solo una sección (requiere
            `section`); "field" extrae solo un campo (requiere `field`).
        mode: "initial" sobrescribe todo; "update" respeta datos existentes y
            completa faltantes; "suggest" genera propuestas sin escribir.
        section: Slug de la sección (ej. "identity", "strategy"). Requerido
            si scope="section".
        field: Path del campo (ej. "identity.brand_name"). Requerido si
            scope="field".
        update_instructions: Texto libre dando pistas al extractor cuando
            mode="update" o mode="suggest".
        entity_id: UUID de la entidad a actualizar. Obligatorio si
            module="offer". Reemplaza al parámetro deprecado offer_id.
        offer_id: [DEPRECADO] UUID de la oferta. Usar entity_id en su lugar.
            Mantenido para compatibilidad con llamadas anteriores.

    Returns:
        JSON con ``status`` ("dispatched" o "error"), ``job_id``,
        ``poll_endpoint``, ``target_label_es``, ``source_kind="url"``,
        ``source_ref``, ``eta_seconds`` y ``message``.

    """
    # Backwards-compat alias: offer_id → entity_id
    resolved_entity_id = entity_id or offer_id

    return await _extract_from_url_impl(
        module=module,
        url=url,
        scope=scope,
        mode=mode,
        section=section,
        field=field,
        update_instructions=update_instructions,
        entity_id=resolved_entity_id,
    )


from luana_core_copilot.application.tools.extract_from_doc import (
    extract_from_doc,
)

EXTRACTION_TOOLS = [extract_from_url, extract_from_doc]

__all__ = ["EXTRACTION_TOOLS", "extract_from_doc", "extract_from_url"]
