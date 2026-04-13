"""
Proactive Nudge Endpoint — returns contextual suggestions based on module completion state.

Uses MODULE_REGISTRY + schema_introspection to detect gaps dynamically.
Caches results in Redis for 5 minutes per tenant+route.
"""

import hashlib
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Query
from sqlalchemy.orm import Session

from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.modules.copilot.api.dto import NudgeContextResponse
from src.modules.copilot.domain.module_registry import ModuleDescriptor, get_module_registry
from src.modules.copilot.domain.schema_introspection import (
    check_section_completion,
    get_model_sections,
)

logger = structlog.get_logger()

router = APIRouter()

# Route prefix → module_id mapping for contextual nudges
ROUTE_MODULE_MAP = {
    "brand-studio": "brand",
    "offer-studio": "offer",
    "connections": "connections",
    "landing": "landing",
    "growth-studio": "analytics",
    "sales": "sales_agent",
}


def _compute_model_completion(data: object, model_class: type) -> float:
    """Compute completion ratio for a Pydantic model-based module."""
    raw = data.model_dump(mode="json")  # type: ignore[union-attr]
    sections = get_model_sections(model_class)
    completion = check_section_completion(raw, sections)
    if not completion:
        return 0.0
    configured = sum(1 for s in completion.values() if s.is_configured)
    return configured / len(completion)


def _get_module_completion_ratio(
    db: Session,
    tenant_id: UUID,
    module_id: str,
    registry: dict[str, ModuleDescriptor],
) -> float | None:
    """Return 0.0-1.0 completion ratio for a module, or None if not readable."""
    descriptor = registry.get(module_id)
    if not descriptor or not descriptor.repo_factory:
        return None

    try:
        repo = descriptor.repo_factory(db)
        data = descriptor.read_fn(repo, tenant_id)
    except Exception:  # noqa: BLE001 — copilot resilience
        return None

    if not data:
        return 0.0

    # List-based modules (offer, connections) — already past `not data` so non-empty
    if isinstance(data, list):
        return 1.0

    # Pydantic-based modules (brand)
    if descriptor.model_class and hasattr(data, "model_dump"):
        return _compute_model_completion(data, descriptor.model_class)

    return 1.0


def _resolve_route_module(route: str | None) -> str | None:
    """Determine which module is relevant to the current route."""
    if not route:
        return None
    route_lower = route.lower()
    for prefix, mod_id in ROUTE_MODULE_MAP.items():
        if prefix in route_lower:
            return mod_id
    return None


def _check_empty_module(
    route_module: str | None,
    completions: dict[str, float],
    registry: dict[str, ModuleDescriptor],
) -> dict | None:
    """Rule 1: EmptyModuleNudge — current route's module is empty."""
    if not route_module or route_module not in completions:
        return None
    if completions[route_module] != 0.0:
        return None
    descriptor = registry.get(route_module)
    if not descriptor:
        return None
    return {
        "id": f"empty_{route_module}",
        "type": "empty_module",
        "module_id": route_module,
        "title": f"Tu {descriptor.label} está vacío",
        "message": f"Configura tu {descriptor.label.lower()} para desbloquear todo el potencial de Nicolify.",
        "suggested_prompt": f"Guíame para configurar mi {descriptor.label.lower()}",
        "priority": 1,
    }


def _check_cross_module_gaps(completions: dict) -> list[dict]:
    """Rules 2-3: CrossModuleGapNudge — brand→offer, offer→connections."""
    nudges: list[dict] = []
    brand_ratio = completions.get("brand", 0.0)
    offer_ratio = completions.get("offer", 0.0)
    conn_ratio = completions.get("connections", 0.0)

    if brand_ratio > 0.3 and offer_ratio == 0.0:
        nudges.append(
            {
                "id": "cross_brand_offer",
                "type": "cross_module_gap",
                "module_id": "offer",
                "title": "Tu marca está configurada, ¿y tus ofertas?",
                "message": "Ya tienes tu identidad de marca definida. El siguiente paso es crear tu primera oferta.",
                "suggested_prompt": "Guíame para crear mi primera oferta",
                "priority": 2,
            },
        )
    if brand_ratio > 0.3 and offer_ratio > 0.0 and conn_ratio == 0.0:
        nudges.append(
            {
                "id": "cross_offer_connections",
                "type": "cross_module_gap",
                "module_id": "connections",
                "title": "Conecta tu primer canal",
                "message": (
                    "Tu marca y ofertas están listas. Conecta Instagram, WhatsApp u otro canal para empezar a vender."
                ),
                "suggested_prompt": "Quiero conectar mi primer canal de ventas",
                "priority": 3,
            },
        )
    return nudges


def _check_incomplete_module(
    route_module: str | None,
    completions: dict[str, float],
    registry: dict[str, ModuleDescriptor],
) -> dict | None:
    """Rule 4: IncompleteModuleNudge — module has <30% completion."""
    if not route_module or route_module not in completions:
        return None
    ratio = completions[route_module]
    if not (0.0 < ratio < 0.3):
        return None
    descriptor = registry.get(route_module)
    if not descriptor:
        return None
    pct = int(ratio * 100)
    return {
        "id": f"incomplete_{route_module}",
        "type": "incomplete_module",
        "module_id": route_module,
        "title": f"Tu {descriptor.label} está al {pct}%",
        "message": f"Completa la configuración de {descriptor.label.lower()} para obtener mejores resultados.",
        "suggested_prompt": f"Ayúdame a completar mi {descriptor.label.lower()}",
        "priority": 4,
    }


def _generate_nudges(tenant_id: UUID, route: str | None) -> list[dict]:
    """Generate nudges based on current module state."""
    registry = get_module_registry()
    db = SessionLocal()
    nudges: list[dict] = []

    try:
        completions = {}
        for mod_id in ["brand", "offer", "connections"]:
            ratio = _get_module_completion_ratio(db, tenant_id, mod_id, registry)
            if ratio is not None:
                completions[mod_id] = ratio

        route_module = _resolve_route_module(route)

        empty = _check_empty_module(route_module, completions, registry)
        if empty:
            nudges.append(empty)

        nudges.extend(_check_cross_module_gaps(completions))

        incomplete = _check_incomplete_module(route_module, completions, registry)
        if incomplete:
            nudges.append(incomplete)

    except Exception as e:  # noqa: BLE001 — copilot resilience
        logger.warning("nudge_generation_error", error=str(e))
    finally:
        db.close()

    nudges.sort(key=lambda n: n.get("priority", 99))
    return nudges


_nudge_cache: dict = {}
_CACHE_TTL = 300  # 5 minutes


def _cache_key(tenant_id: UUID, route: str | None) -> str:
    route_hash = hashlib.md5((route or "").encode()).hexdigest()[:8]
    return f"copilot:nudge:{tenant_id}:{route_hash}"


@router.get("/nudge-context", response_model=NudgeContextResponse)
def get_nudge_context(route: Annotated[str | None, Query()] = None) -> dict:
    """Return proactive nudges based on module completion state and current route."""
    import time

    tenant_id = get_tenant_id()
    if not tenant_id:
        return {"nudges": []}

    key = _cache_key(tenant_id, route)
    now = time.time()

    # Check in-memory cache
    cached = _nudge_cache.get(key)
    if cached and (now - cached["ts"]) < _CACHE_TTL:
        return {"nudges": cached["data"]}

    nudges = _generate_nudges(tenant_id, route)

    # Store in cache
    _nudge_cache[key] = {"data": nudges, "ts": now}

    return {"nudges": nudges}
