"""Outbound asset tools — let the LLM reference existing tenant assets.

# [COPILOT-OUTBOUND-ASSETS] → docs/domains/copilot/outbound-assets.md

The assistant uses these tools to find and reference assets (images, audio,
video, documents) already stored in the assets module. It NEVER generates
media — it only references real Asset rows via their public_url.

System-prompt guidance (injected via skill loader):
    Cuando el usuario te pida una imagen, audio, video o documento que ya subió,
    llama primero a ``search_assets`` con una consulta descriptiva.
    NUNCA inventes URLs o IDs de assets.
    Usa solo los valores de ``asset_id`` y ``public_url`` que devuelve la tool.

Guardrails:
- tenant_id comes from request context (never from LLM arguments).
- storage_path is never returned (internal R2 key).
- Soft-deleted assets (deleted_at IS NOT NULL) are excluded.
- limit capped at 20 to avoid token bloat.

See docs/domains/copilot/outbound-assets.md for the full spec.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from langchain_core.tools import tool
from sqlalchemy import or_, select

from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.modules.assets.infrastructure.models.asset_model import AssetModel
from src.modules.assets.infrastructure.repositories.asset_repository import (
    AssetRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()

# Max results cap to prevent token bloat (CONTRACT-MULTIMODAL §8.6)
_MAX_LIMIT = 20


def _kind_to_asset_type(kind: str | None) -> str | None:
    """Convert public 'kind' string to AssetType enum value."""
    mapping = {
        "image": "IMAGE",
        "audio": "AUDIO",
        "video": "VIDEO",
        "document": "DOCUMENT",
    }
    return mapping.get(kind) if kind else None


def _asset_to_ref(asset: object) -> dict:
    """Convert an Asset domain entity or model to a public AssetRef dict.

    storage_path is intentionally excluded (internal R2 key — never exposed).
    """
    # Works with both domain entity and ORM model via duck typing
    kind_raw = getattr(asset, "type", "IMAGE")
    kind_map = {"IMAGE": "image", "AUDIO": "audio", "VIDEO": "video", "DOCUMENT": "document"}
    kind = kind_map.get(str(kind_raw).upper(), "document")

    description = getattr(asset, "user_description", None) or getattr(asset, "ai_description", None) or ""

    return {
        "asset_id": str(asset.id),
        "public_url": str(asset.public_url),
        "mime": str(getattr(asset, "mime_type", "") or ""),
        "kind": kind,
        "filename": str(getattr(asset, "filename", "") or ""),
        "description": description,
    }


def _search_assets_query(
    db: Session,
    tenant_id: UUID,
    query: str,
    kind: str | None = None,
    offer_id: UUID | None = None,
    limit: int = 5,
) -> list:
    """Execute a free-text search over tenant assets in the DB.

    Searched fields: user_description, ai_description, filename.
    JSONB ai_metadata.tags search is deferred (requires GIN index).
    """
    effective_limit = min(limit, _MAX_LIMIT)
    asset_type = _kind_to_asset_type(kind)

    stmt = select(AssetModel).where(
        AssetModel.tenant_id == tenant_id,
        AssetModel.deleted_at.is_(None),
        # Anti-pollution: ``ephemeral`` assets are chat-scoped context and
        # must NOT show up as reusable library items. Only library and
        # deliverable assets are discoverable.
        AssetModel.scope.in_(("library", "deliverable")),
    )

    if asset_type:
        stmt = stmt.where(AssetModel.type == asset_type)

    if offer_id:
        stmt = stmt.where(AssetModel.offer_id == offer_id)

    if query:
        q = f"%{query}%"
        stmt = stmt.where(
            or_(
                AssetModel.user_description.ilike(q),
                AssetModel.ai_description.ilike(q),
                AssetModel.filename.ilike(q),
            )
        )

    stmt = stmt.limit(effective_limit)
    models = db.execute(stmt).scalars().all()
    return list(models)


@tool
def search_assets(
    query: str,
    kind: str | None = None,
    offer_id: str | None = None,
    limit: int = 5,
) -> str:
    """Busca en los assets del tenant por query de texto libre.

    Args:
        query: Consulta en lenguaje natural (e.g. "flyer lanzamiento", "foto perfil").
        kind: Filtro opcional de tipo: "image", "audio", "video", "document".
        offer_id: UUID opcional para limitar la búsqueda a una oferta específica.
        limit: Número máximo de resultados (1..20, default 5).

    Returns:
        JSON array de AssetRef con asset_id, public_url, mime, kind, filename, description.
        Retorna lista vacía [] si no hay resultados.
        Retorna JSON con campo "error" si hay un problema.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        logger.warning("search_assets_no_tenant_context")
        return json.dumps({"error": "No se pudo determinar el contexto del tenant."})

    effective_limit = max(1, min(limit, _MAX_LIMIT))
    parsed_offer_id: UUID | None = None
    if offer_id:
        try:
            parsed_offer_id = UUID(offer_id)
        except ValueError:
            return json.dumps({"error": f"offer_id inválido: {offer_id}"})

    try:
        with SessionLocal() as db:
            # Use our inline search query (AssetRepository doesn't have search_by_query yet)
            models = _search_assets_query(
                db,
                tenant_id=tenant_id,
                query=query,
                kind=kind,
                offer_id=parsed_offer_id,
                limit=effective_limit,
            )
            results = [_asset_to_ref(m) for m in models]

        logger.info(
            "search_assets_completed",
            tenant_id=str(tenant_id),
            query=query,
            kind=kind,
            results_count=len(results),
        )
        return json.dumps(results, ensure_ascii=False)

    except Exception:
        logger.exception("search_assets_error", tenant_id=str(tenant_id), query=query)
        return json.dumps({"error": "Error buscando assets. Intenta de nuevo."})


@tool
def get_asset(asset_id: str) -> str:
    """Obtiene un asset específico por su ID.

    Args:
        asset_id: UUID del asset a obtener.

    Returns:
        JSON con el AssetRef si se encontró, o {"error": "not_found"} si no existe
        o pertenece a otro tenant. El error "not_found" oculta la existencia
        de assets de otros tenants (guardrail de privacidad).

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        logger.warning("get_asset_no_tenant_context")
        return json.dumps({"error": "No se pudo determinar el contexto del tenant."})

    try:
        parsed_id = UUID(asset_id)
    except ValueError:
        return json.dumps({"error": "not_found"})

    try:
        with SessionLocal() as db:
            repo = AssetRepository(db)
            asset = repo.get_by_id(parsed_id, tenant_id=tenant_id)

        if not asset:
            # Return "not_found" for both true 404 and cross-tenant (avoid leaking existence)
            logger.info("get_asset_not_found", tenant_id=str(tenant_id), asset_id=asset_id)
            return json.dumps({"error": "not_found"})

        result = _asset_to_ref(asset)
        logger.info(
            "get_asset_completed",
            tenant_id=str(tenant_id),
            asset_id=asset_id,
        )
        return json.dumps(result, ensure_ascii=False)

    except Exception:
        logger.exception("get_asset_error", tenant_id=str(tenant_id), asset_id=asset_id)
        return json.dumps({"error": "not_found"})


ASSETS_TOOLS = [search_assets, get_asset]

__all__ = ["ASSETS_TOOLS", "get_asset", "search_assets"]
