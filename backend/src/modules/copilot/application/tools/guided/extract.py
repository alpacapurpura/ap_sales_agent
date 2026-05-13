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
from luana_core_copilot.domain.extraction_domain_registry import (
    get_extraction_config,
    supported_domains,
)
from luana_core_copilot.domain.schema_introspection import validate_field_path
from luana_core_platform.application.ai_action_service import AIActionService
from luana_core_platform.core.context import get_tenant_id
from luana_core_platform.core.database import SessionLocal

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
            "llm_content": (
                f"La extracción del documento falló ({code}). El usuario "
                "ya ve una tarjeta con las opciones Reintentar / Subir otro "
                "documento / Llenar manualmente. NO describas el error con "
                "detalle técnico. Escribe una sola línea breve invitando a "
                "elegir una opción."
            ),
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
        JSON con ``delta`` (silent capture, sin ui_action), ``skipped``
        (field_paths inválidos descartados por no pertenecer al esquema)
        y ``confidence_map`` (campos con baja confianza). Sin card visible
        — la herramienta es silenciosa por diseño. El LLM puede reaccionar
        leyendo el delta del ToolMessage para guiar el siguiente turno.

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
            "domain": domain,
            "delta": delta,
            "confidence_map": confidence_map,
            "skipped": skipped,
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
    dominio. El resultado se refleja via ``ProposalCard`` (ui_action
    ``proposal``) y el usuario puede aceptar/rechazar individualmente o
    en batch.

    Args:
        asset_id: UUID del asset subido (disponible en el contexto adjunto).
        domain: "brand" | "offer" | "buyer_persona".
        entity_id: UUID de la entidad si el dominio lo requiere (offer,
            buyer_persona). Opcional para brand.

    Returns:
        JSON con un resumen textual breve + ui_action ``proposal`` con el
        listado de ``updates`` (mismo shape que ``propose_field_updates``),
        o un error claro si no pudo procesar. ``ProposalCard`` lo renderea
        colapsable con per-field Aceptar/Rechazar + Aceptar todos.

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
        from luana_core_assets.infrastructure.repositories.asset_repository import (
            AssetRepository,
        )
        from luana_core_copilot.application.services.document_processor import (
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

        section_names = sorted({k.split(".", 1)[0] for k in delta})
        sections_hint = ", ".join(section_names) if section_names else "varias secciones"

        # ``new_value`` carries the raw Python value (str / list / dict /
        # number). Pydantic ``ApplyMutationUpdate.new_value: object | None``
        # accepts any JSON shape on the wire, the FE renders structurally
        # per type, and ``bridge.patchField`` (typed ``unknown``) forwards
        # it to the form-runtime which expects native shapes (e.g.
        # ``pain_points`` is a list of objects, NOT a JSON-stringified
        # blob). JSON-coercion broke schema validation for every multi-
        # value field. Single source of truth = raw values end-to-end.
        updates = [
            {
                "field_id": field_path,
                "new_value": value,
                "reason": "Extraído del documento adjunto",
            }
            for field_path, value in delta.items()
        ]

        return json.dumps(
            {
                "text": (
                    f"Extraje {fields_extracted} campo(s) del documento "
                    f"'{asset.filename}'. Revisa la propuesta y acéptala."
                ),
                # ``llm_content`` is the condensed view the model sees in its
                # next turn — keeps the raw delta out of the context window
                # so the LLM cannot copy-paste field values into chat.
                "llm_content": (
                    f"Extracción exitosa: {fields_extracted} campo(s) del "
                    f"documento '{asset.filename}' repartidos en {sections_hint}. "
                    "El usuario ya ve la propuesta con los valores y los "
                    "botones Aceptar/Rechazar; NO los repitas en tu respuesta. "
                    "Responde en UNA línea corta invitando a revisar y aplicar."
                ),
                "ui_action": {
                    "type": "proposal",
                    "updates": updates,
                    "domain": domain,
                    "entity_id": entity_id,
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
