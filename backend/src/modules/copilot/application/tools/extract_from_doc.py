"""Conversational extraction tool — ingest an asset document into Brand/Offer/Persona Studio.

Wraps the existing ``extract_document_to_fields`` under ``guided/extract.py``
with the unified AsyncToolJob contract defined in FLOW-SPEC §3.1 and §3.2.

Unlike ``extract_from_url`` (which dispatches an ARQ job for long-running URL scraping),
this tool runs document extraction synchronously via the existing DocumentProcessor
pipeline and returns the same AsyncToolJob shape for frontend consistency.

The async appearance (job_id + poll_endpoint) is intentional: the frontend polling
infrastructure is reused so the ToolCallChip, progress, and summary card flows work
without special-casing doc vs URL sources.

Tenant isolation: tenant_id is read from ``get_tenant_id()`` (request-scoped
ContextVar), never taken as a tool argument.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

import structlog
from langchain_core.tools import tool

from src.core.context import get_conversation_id, get_tenant_id
from src.core.database import redis_client

logger = structlog.get_logger()

# Import the ARQ pool — may be None when the worker is unavailable
try:
    from src.core.arq_pool import get_arq_pool as _get_arq_pool
except ImportError:  # pragma: no cover — optional dependency
    _get_arq_pool = lambda: None  # noqa: E731


def _err(message: str, **extra: object) -> str:
    """Shape an error payload matching the tool contract envelope."""
    return json.dumps({"status": "error", "message": message, **extra})


# Human-readable module labels (Spanish LatAm neutro)
_MODULE_LABELS: dict[str, str] = {
    "brand": "Brand Studio",
    "offer": "Offer Studio",
    "asset": "Assets",
    "persona": "Buyer Persona",
}

# Section label maps (same as extraction_tools for consistency)
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

_DOCUMENT_EXTRACTION_TEMPLATES: dict[str, str] = {
    "brand": "brand_doc_extraction",
    "offer": "offer_doc_extraction",
    "buyer_persona": "buyer_persona_doc_extraction",
}


_OFFER_SECTION_LABELS: dict[str, str] = {
    "promise": "Promesa",
    "details": "Detalles",
    "strategy": "Estrategia",
    "psychology": "Psicología",
    "value-stack": "Stack de Valor",
    "value_stack": "Stack de Valor",
    "closing": "Cierre",
}


def _compose_target_label(module: str, scope: str, section: str | None) -> str:
    """Build a user-facing label for the extraction target."""
    module_label = _MODULE_LABELS.get(module, module.replace("_", " ").title())
    if scope in ("section", "field") and section:
        section_label = (
            _BRAND_SECTION_LABELS.get(section)
            or _OFFER_SECTION_LABELS.get(section)
            or section.replace("-", " ").replace("_", " ").title()
        )
        return f"{module_label} · {section_label}"
    return module_label


@tool
async def extract_from_doc(
    module: Literal["brand", "offer", "asset", "persona"],
    asset_id: str,
    scope: Literal["full", "section", "field"] = "full",
    mode: Literal["initial", "update", "suggest"] = "initial",
    section: str | None = None,
    field: str | None = None,
    update_instructions: str | None = None,
    entity_id: str | None = None,
) -> str:
    """Extrae datos de un documento adjunto hacia Brand Studio, Offer Studio o Persona.

    Úsalo cuando el usuario sube un brief, propuesta, presentación, o cualquier
    documento con información para múltiples campos. Lee el texto extraído del
    asset existente y popula los campos del módulo seleccionado.

    IMPORTANTE — Antes de llamar esta tool:

    Si el usuario no especificó el alcance, llama primero a ``clarify`` con:
      1. Alcance (fieldPath="__scope__"):
         options: ["Solo {sección actual}", "Todo {módulo}", "Solo una sección…"]
      2. Modo (fieldPath="__mode__"):
         options: ["Solo llenar vacíos", "Reemplazar todo", "Sugerir (no escribir)"]

    Nota: scope="visuals" NO está disponible para documentos — los documentos
    no contienen elementos visuales extraíbles. Usa extract_from_url si necesitas
    extraer colores, tipografías u otros elementos visuales.

    Args:
        module: Studio destino. "brand", "offer", "asset" o "persona".
        asset_id: UUID del asset subido (disponible en el contexto adjunto del
            usuario o via ``list_assets``).
        scope: "full" extrae toda la información del módulo; "section" extrae
            solo una sección (requiere `section`); "field" extrae solo un campo
            (requiere `field`). NOTE: "visuals" NO es válido aquí.
        mode: "initial" sobrescribe; "update" respeta existentes y completa
            faltantes; "suggest" genera propuestas sin escribir.
        section: Slug de la sección. Requerido si scope="section".
        field: Path del campo. Requerido si scope="field".
        update_instructions: Texto libre con pistas para el extractor.
        entity_id: UUID de la entidad a actualizar. Obligatorio si
            module="offer".

    Returns:
        JSON con ``status`` ("dispatched" o "error"), ``job_id``,
        ``poll_endpoint``, ``target_label_es``, ``source_kind="doc"``,
        ``source_ref=asset_id``, ``eta_seconds`` y ``message``.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        return _err("No hay contexto de tenant. Vuelve a iniciar sesión.")

    # Validate asset_id
    try:
        UUID(asset_id)
    except (ValueError, TypeError):
        return _err(f"asset_id inválido: {asset_id!r}. Debe ser un UUID válido.")

    # Validate scope — no visuals for docs
    if scope == "visuals":  # type: ignore[comparison-overlap]
        return _err(
            "El scope 'visuals' no está disponible para documentos. "
            "Usa extract_from_url para extraer elementos visuales desde una URL.",
        )

    if scope == "section" and not section:
        return _err(
            "El scope 'section' requiere el parámetro 'section' con el slug de la sección.",
        )
    if scope == "field" and not field:
        return _err(
            "El scope 'field' requiere el parámetro 'field' con el path del campo.",
        )

    if module == "offer" and not entity_id:
        return _err(
            "Falta entity_id. Identifica la oferta antes de extraer desde un documento.",
        )

    # Check Redis is available (for progress tracking)
    if redis_client is None:
        return _err("No se puede registrar el progreso. Intenta de nuevo.")

    # Map module to domain for extract_document_to_fields
    domain_map = {
        "brand": "brand",
        "offer": "offer",
        "persona": "buyer_persona",
        "asset": "brand",  # fallback — assets don't have their own extraction template yet
    }
    domain = domain_map.get(module, "brand")

    job_id = str(uuid4())
    tenant_str = str(tenant_id)
    started_at = datetime.now(UTC).isoformat()
    target_label_es = _compose_target_label(module, scope, section)

    # Set up Redis progress key
    progress_key = f"extract:{tenant_str}:{module}:{job_id}"
    redis_client.setex(
        progress_key,
        3600,
        json.dumps(
            {
                "status": "queued",
                "progress": 0,
                "stage": "Iniciando extracción del documento...",
                "started_at": started_at,
                "filled_fields": [],
                "filled_fields_by_section": {},
                "sections_touched": [],
                "sections_completed": [],
                "newly_completed_section": None,
            },
        ),
    )

    # Run document extraction inline (synchronous — documents are already stored)
    # This uses the same pipeline as extract_document_to_fields but returns the
    # unified AsyncToolJob shape for frontend consistency.
    try:
        from src.core.database import SessionLocal
        from src.modules.assets.infrastructure.repositories.asset_repository import (
            AssetRepository,
        )
        from src.modules.copilot.application.services.document_processor import (
            DocumentProcessor,
        )
        from src.shared.application.ai_action_service import AIActionService

        template = _DOCUMENT_EXTRACTION_TEMPLATES.get(domain)
        if not template:
            return _err(f"El módulo '{module}' no tiene template de extracción de documentos.")

        db = SessionLocal()
        try:
            asset_repo = AssetRepository(db)
            asset = asset_repo.get_by_id(UUID(asset_id), tenant_id=tenant_id)
            if asset is None:
                redis_client.setex(
                    progress_key,
                    3600,
                    json.dumps({"status": "failed", "progress": 0, "error": "Asset no encontrado."}),
                )
                return _err(f"No se encontró el asset {asset_id}.", asset_id=asset_id)

            text = (asset.extracted_text or "").strip()
            if not text:
                redis_client.setex(
                    progress_key,
                    3600,
                    json.dumps({"status": "failed", "progress": 0, "error": "Documento sin texto extraído."}),
                )
                return _err(
                    f"El documento '{asset.filename}' aún no tiene texto extraído. "
                    "Espera unos segundos y vuelve a intentarlo.",
                    asset_id=asset_id,
                )

            # Update progress: processing
            redis_client.setex(
                progress_key,
                3600,
                json.dumps(
                    {
                        "status": "processing",
                        "progress": 30,
                        "stage": f"Analizando documento '{asset.filename}'...",
                        "started_at": started_at,
                        "filled_fields": [],
                        "filled_fields_by_section": {},
                        "sections_touched": [],
                        "sections_completed": [],
                        "newly_completed_section": None,
                    },
                ),
            )

            processor = DocumentProcessor(ai_service=AIActionService())
            result = processor.extract_from_text(
                text=text,
                source_documents=[asset.filename or "documento"],
                extraction_template=template,
                existing_mapa={},
                tenant_id=tenant_id,
            )

            fields_extracted = result.fields_extracted if result else 0
            filled_fields = list((result.delta or {}).keys()) if result else []

            # Compute section grouping from filled_fields (naive: split on first dot)
            filled_by_section: dict[str, list[str]] = {}
            for fp in filled_fields:
                parts = fp.split(".", 1)
                sec = parts[0] if len(parts) > 1 else "__root__"
                filled_by_section.setdefault(sec, []).append(fp)

            sections_completed = list(filled_by_section.keys()) if filled_by_section else []

            # Mark completed
            finished_at = datetime.now(UTC).isoformat()
            redis_client.setex(
                progress_key,
                3600,
                json.dumps(
                    {
                        "status": "completed",
                        "progress": 100,
                        "stage": f"¡Extracción completada! {fields_extracted} campos extraídos.",
                        "started_at": started_at,
                        "finished_at": finished_at,
                        "filled_fields": filled_fields,
                        "filled_fields_by_section": filled_by_section,
                        "sections_touched": sections_completed,
                        "sections_completed": sections_completed,
                        "newly_completed_section": None,
                    },
                ),
            )

            # Publish section + job completion events so the copilot subscriber
            # emits the extraction_summary card + nav pills, matching the
            # brand/offer URL worker contract.
            _publish_completion_events(
                tenant_id=tenant_str,
                job_id=job_id,
                conversation_id=get_conversation_id(),
                module=module,
                source_ref=asset_id,
                started_at=started_at,
                finished_at=finished_at,
                filled_fields=filled_fields,
                filled_by_section=filled_by_section,
                sections_completed=sections_completed,
            )

        finally:
            db.close()

    except Exception as exc:
        logger.exception(
            "extract_from_doc_failed",
            asset_id=asset_id,
            module=module,
            job_id=job_id,
        )
        if redis_client:
            redis_client.setex(
                progress_key,
                3600,
                json.dumps({"status": "failed", "progress": 0, "error": str(exc)}),
            )

    # Determine poll endpoint (brand-studio compatible endpoint)
    poll_endpoint_map = {
        "brand": f"/api/v1/brand/extract-full-brand/status/{job_id}",
        "offer": f"/api/v1/offer/extract-full-offer/status/{job_id}",
    }
    poll_endpoint = poll_endpoint_map.get(module, f"/api/v1/brand/extract-full-brand/status/{job_id}")

    # Store in canonical key format too (for backwards compat status lookup)
    legacy_key = f"{module}_extract:{tenant_str}:{job_id}"
    if redis_client:
        # Copy to legacy key so existing status endpoints can read it
        current = redis_client.get(progress_key)
        if current:
            redis_client.setex(legacy_key, 3600, current)

    logger.info(
        "copilot_extract_from_doc_dispatched",
        module=module,
        tenant_id=tenant_str,
        job_id=job_id,
        asset_id=asset_id,
        scope=scope,
        mode=mode,
    )

    friendly = "Extraje los campos del documento. Revisa el resumen para ver qué se completó."

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
            "source_kind": "doc",
            "source_ref": asset_id,
            "eta_seconds": 30,
            "message": friendly,
        },
    )


def _publish_completion_events(
    *,
    tenant_id: str,
    job_id: str,
    conversation_id: str | None,
    module: str,
    source_ref: str,
    started_at: str,
    finished_at: str,
    filled_fields: list[str],
    filled_by_section: dict[str, list[str]],
    sections_completed: list[str],
) -> None:
    """Publish section + job events. Exceptions swallowed so cards never kill extraction."""
    if not conversation_id:
        return
    try:
        from src.shared.domain.events import (
            EventBus,
            ExtractionJobCompletedEvent,
            ExtractionSectionCompletedEvent,
        )

        started_dt = datetime.fromisoformat(started_at)
        finished_dt = datetime.fromisoformat(finished_at)
        duration_s = int((finished_dt - started_dt).total_seconds())

        for section_slug in sections_completed:
            section_fields = filled_by_section.get(section_slug, [])
            EventBus.publish(
                ExtractionSectionCompletedEvent.create(
                    tenant_id=UUID(tenant_id),
                    job_id=job_id,
                    conversation_id=conversation_id,
                    module=module,
                    section_slug=section_slug,
                    section_label=_resolve_section_label(section_slug, module),
                    fields_count=len(section_fields),
                ),
                session=None,
            )

        EventBus.publish(
            ExtractionJobCompletedEvent.create(
                tenant_id=UUID(tenant_id),
                job_id=job_id,
                conversation_id=conversation_id,
                module=module,
                source_ref=source_ref,
                duration_seconds=duration_s,
                filled_fields=list(filled_fields),
                filled_fields_by_section=dict(filled_by_section),
                sections_completed=list(sections_completed),
            ),
            session=None,
        )
    except Exception:  # noqa: BLE001 — card emission must not fail extraction
        logger.warning(
            "extract_from_doc_event_publication_failed",
            exc_info=True,
            job_id=job_id,
            conversation_id=conversation_id,
        )


def _resolve_section_label(slug: str, module: str) -> str:
    """Resolve a section slug to a Spanish label. Fallback to titlecased slug."""
    labels = _BRAND_SECTION_LABELS if module == "brand" else _OFFER_SECTION_LABELS
    return labels.get(slug, slug.replace("-", " ").replace("_", " ").title())


__all__ = ["extract_from_doc"]
