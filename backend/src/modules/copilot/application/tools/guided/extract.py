"""Field-extraction tools shared by guided and free copilot modes.

``extract_structured`` is the silent per-turn extractor (replaces the old
interview tool without the ``session_id`` argument). ``extract_document_to_fields``
runs the bulk document → multi-section extraction that used to live behind
``POST /api/v1/copilot/interview/{id}/documents``; it's now a tool so the LLM
can invoke it from any conversation, guided or not.
"""

from __future__ import annotations

import json
from uuid import UUID

import structlog
from langchain_core.tools import tool

from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.modules.copilot.domain.extraction_domain_registry import (
    get_extraction_config,
    supported_domains,
)
from src.modules.copilot.domain.schema_introspection import validate_field_path
from src.shared.application.ai_action_service import AIActionService

logger = structlog.get_logger()


def _error(text: str, code: str) -> str:
    """Serialise a short error payload for a failed extraction attempt."""
    return json.dumps({"text": text, "error": code})


def _recovery_card(text: str, code: str, domain: str) -> str:
    """Surface a `clarify_card` so the LLM has a structured next step.

    When document extraction fails (LLM hallucinated paths, asset not yet
    extracted, transient API error) the chat would otherwise show either
    the raw error or — much worse — the LLM's regurgitation of the
    document text as fake JSON. The clarify card gives the model a clear
    branch to pick from and keeps the user in flow.
    """
    return json.dumps(
        {
            "text": text,
            "error": code,
            "ui_action": {
                "type": "clarify_card",
                "clarify_items": [
                    {
                        "field_path": f"{domain}.__doc_recovery__",
                        "issue": "No pude extraer datos útiles del documento. ¿Qué quieres hacer?",
                        "options": [
                            "Reintentar",
                            "Subir otro documento",
                            "Llenar manualmente",
                        ],
                    },
                ],
            },
        },
    )


@tool
def extract_structured(domain: str, extractions: list[dict]) -> str:
    """Captura datos estructurados del mensaje del usuario (silencioso).

    Invocar CADA TURNO donde el usuario aporte información factual. La
    herramienta es silenciosa — no genera texto visible. Captura datos de
    CUALQUIER sección, aunque no sea el bloque actual.

    Args:
        domain: Dominio de la entidad ("brand", "offer", "buyer_persona").
        extractions: Lista de ítems. Cada uno con:
            - field_path: Dot-notation (ej "identity.brand_name",
              "pricing_options"). Aceptado si existe en el esquema del dominio.
            - value: El valor extraído (string, list o dict).
            - confidence: Float 0.0-1.0. <0.8 = pendiente de aclarar.
            - source: "user_explicit" | "inferred" | "recommended"

    Returns:
        JSON con ui_action ``preview_update`` que incluye el delta y los
        field_paths descartados por no pertenecer al esquema.

    """
    delta: dict[str, object] = {}
    confidence_map: dict[str, float] = {}
    skipped: list[str] = []

    for item in extractions:
        field_path = item.get("field_path", "")
        value = item.get("value")
        confidence = float(item.get("confidence", 1.0))

        if not field_path or value is None:
            continue

        if not validate_field_path(domain, field_path):
            skipped.append(field_path)
            continue

        delta[field_path] = value
        if confidence < 0.8:
            confidence_map[field_path] = confidence

    text_msg = ""
    if skipped and not delta:
        skipped_list = ", ".join(f"`{p}`" for p in skipped)
        text_msg = (
            f"Ninguno de los field_paths propuestos es válido en el dominio '{domain}': "
            f"{skipped_list}. Revisa el catálogo editable y reintenta con paths existentes. "
            "Si el campo ya está lleno, NO repitas el mismo extract_structured — "
            "continúa con otro campo pendiente del bloque actual."
        )

    return json.dumps(
        {
            "text": text_msg,
            "ui_action": {
                "type": "preview_update",
                "domain": domain,
                "delta": delta,
                "confidence_map": confidence_map,
                "skipped": skipped,
            },
        },
    )


@tool
def extract_document_to_fields(  # noqa: PLR0911 — each return is a distinct tool-level error state
    asset_id: str,
    domain: str,
    entity_id: str | None = None,
) -> str:
    """Extrae de un documento adjunto datos para TODAS las secciones del dominio.

    Úsalo cuando el usuario sube un brief, propuesta, o cualquier doc que
    contenga información para varios campos a la vez. Lee el texto extraído
    del asset (asset_lifecycle) y llama al extractor AI con el template del
    dominio. El resultado se refleja via ``preview_update`` y el copilot
    puede proponer los cambios con ``propose_field_updates``.

    Args:
        asset_id: UUID del asset subido (disponible en el contexto adjunto).
        domain: "brand" | "offer" | "buyer_persona".
        entity_id: UUID de la entidad si el dominio lo requiere (offer,
            buyer_persona). Opcional para brand.

    Returns:
        JSON con un resumen textual breve + ui_action ``preview_update`` con
        el delta combinado, o un error claro si no pudo procesar.

    """
    if get_extraction_config(domain) is None:
        supported = ", ".join(supported_domains())
        return _error(
            f"Dominio '{domain}' no soporta extracción de documentos. Soportados: {supported}.",
            "unsupported_domain",
        )

    tenant_id = get_tenant_id()
    if not tenant_id:
        return _error("No se pudo identificar el tenant.", "missing_tenant")

    try:
        asset_uuid = UUID(asset_id)
    except (ValueError, TypeError):
        return _error(f"asset_id inválido: {asset_id!r}.", "bad_asset_id")

    db = SessionLocal()
    try:
        from src.modules.assets.infrastructure.repositories.asset_repository import (
            AssetRepository,
        )
        from src.modules.copilot.application.services.document_processor import (
            DocumentProcessor,
        )

        asset_repo = AssetRepository(db)
        asset = asset_repo.get_by_id(asset_uuid, tenant_id=tenant_id)
        if asset is None:
            return _error(f"No se encontró el asset {asset_id}.", "asset_not_found")

        text = (asset.extracted_text or "").strip()
        if not text:
            return _error(
                (
                    f"El asset '{asset.filename}' aún no tiene texto extraído. "
                    "Pide al usuario que lo suba de nuevo en unos segundos."
                ),
                "asset_not_extracted",
            )

        processor = DocumentProcessor(ai_service=AIActionService())

        result = processor.extract_from_text(
            text=text,
            source_documents=[asset.filename or "documento"],
            domain=domain,
            existing_mapa={},
            tenant_id=tenant_id,
        )

        delta = result.delta if result else {}
        fields_extracted = result.fields_extracted if result else 0
        fields_skipped = result.fields_skipped if result else 0

        # No fields extracted is a soft failure: surface a clarify card so
        # the LLM offers retry/manual instead of inventing JSON in chat.
        if fields_extracted == 0:
            return _recovery_card(
                f"No logré extraer campos útiles del documento '{asset.filename}'.",
                "no_fields_extracted",
                domain,
            )

        return json.dumps(
            {
                "text": (
                    f"Extraje {fields_extracted} campo(s) del documento "
                    f"'{asset.filename}'. Revisa el preview para aprobarlos."
                ),
                "ui_action": {
                    "type": "preview_update",
                    "domain": domain,
                    "entity_id": entity_id,
                    "delta": delta,
                    "skipped": [],
                    "summary": result.summary if result else None,
                    "source_documents": (result.source_documents if result else []),
                    "fields_extracted": fields_extracted,
                    "fields_skipped": fields_skipped,
                },
            },
            default=str,
        )
    except Exception as exc:
        logger.exception("extract_document_to_fields_failed", asset_id=asset_id, domain=domain)
        return _recovery_card(
            f"Hubo un problema procesando el documento: {exc}",
            "extraction_failed",
            domain,
        )
    finally:
        db.close()
