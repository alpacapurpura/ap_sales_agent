"""
Proactive Nudge Endpoint — returns contextual suggestions based on module completion state.

Uses MODULE_REGISTRY + schema_introspection to detect gaps dynamically.
Caches results in Redis for 5 minutes per tenant+route.
"""

import hashlib
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Query

from src.core.context import get_tenant_id
from src.core.database import SessionLocal
from src.modules.copilot.domain.module_registry import get_module_registry
from src.modules.copilot.domain.schema_introspection import (
    check_section_completion,
    get_model_sections,
)

import structlog

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


def _get_module_completion_ratio(db, tenant_id: UUID, module_id: str, registry) -> Optional[float]:
    """Return 0.0-1.0 completion ratio for a module, or None if not readable."""
    descriptor = registry.get(module_id)
    if not descriptor or not descriptor.repo_factory:
        return None

    try:
        repo = descriptor.repo_factory(db)
        data = descriptor.read_fn(repo, tenant_id)
    except Exception:
        return None

    if not data:
        return 0.0

    # List-based modules (offer, connections)
    if isinstance(data, list):
        return 1.0 if len(data) > 0 else 0.0

    # Pydantic-based modules (brand)
    if descriptor.model_class and hasattr(data, "model_dump"):
        raw = data.model_dump(mode="json")
        sections = get_model_sections(descriptor.model_class)
        completion = check_section_completion(raw, sections)
        if not completion:
            return 0.0
        configured = sum(1 for s in completion.values() if s.is_configured)
        return configured / len(completion) if completion else 0.0

    return 1.0


def _generate_nudges(tenant_id: UUID, route: Optional[str]) -> List[dict]:
    """Generate nudges based on current module state."""
    registry = get_module_registry()
    db = SessionLocal()
    nudges = []

    try:
        # Compute completion for key modules
        completions = {}
        for mod_id in ["brand", "offer", "connections"]:
            ratio = _get_module_completion_ratio(db, tenant_id, mod_id, registry)
            if ratio is not None:
                completions[mod_id] = ratio

        # Determine which module is relevant to the current route
        route_module = None
        if route:
            route_lower = route.lower()
            for prefix, mod_id in ROUTE_MODULE_MAP.items():
                if prefix in route_lower:
                    route_module = mod_id
                    break

        # Rule 1: EmptyModuleNudge — current route's module is empty
        if route_module and route_module in completions and completions[route_module] == 0.0:
            descriptor = registry.get(route_module)
            if descriptor:
                nudges.append({
                    "id": f"empty_{route_module}",
                    "type": "empty_module",
                    "module_id": route_module,
                    "title": f"Tu {descriptor.label} está vacío",
                    "message": f"Configura tu {descriptor.label.lower()} para desbloquear todo el potencial de Nicolify.",
                    "suggested_prompt": f"Guíame para configurar mi {descriptor.label.lower()}",
                    "priority": 1,
                })

        # Rule 2: CrossModuleGapNudge — brand has data but offer doesn't
        brand_ratio = completions.get("brand", 0.0)
        offer_ratio = completions.get("offer", 0.0)
        if brand_ratio > 0.3 and offer_ratio == 0.0:
            nudges.append({
                "id": "cross_brand_offer",
                "type": "cross_module_gap",
                "module_id": "offer",
                "title": "Tu marca está configurada, ¿y tus ofertas?",
                "message": "Ya tienes tu identidad de marca definida. El siguiente paso es crear tu primera oferta.",
                "suggested_prompt": "Guíame para crear mi primera oferta",
                "priority": 2,
            })

        # Rule 3: CrossModuleGapNudge — brand + offer ready but no connections
        conn_ratio = completions.get("connections", 0.0)
        if brand_ratio > 0.3 and offer_ratio > 0.0 and conn_ratio == 0.0:
            nudges.append({
                "id": "cross_offer_connections",
                "type": "cross_module_gap",
                "module_id": "connections",
                "title": "Conecta tu primer canal",
                "message": "Tu marca y ofertas están listas. Conecta Instagram, WhatsApp u otro canal para empezar a vender.",
                "suggested_prompt": "Quiero conectar mi primer canal de ventas",
                "priority": 3,
            })

        # Rule 4: IncompleteModuleNudge — module has <30% completion
        if route_module and route_module in completions:
            ratio = completions[route_module]
            if 0.0 < ratio < 0.3:
                descriptor = registry.get(route_module)
                if descriptor:
                    pct = int(ratio * 100)
                    nudges.append({
                        "id": f"incomplete_{route_module}",
                        "type": "incomplete_module",
                        "module_id": route_module,
                        "title": f"Tu {descriptor.label} está al {pct}%",
                        "message": f"Completa la configuración de {descriptor.label.lower()} para obtener mejores resultados.",
                        "suggested_prompt": f"Ayúdame a completar mi {descriptor.label.lower()}",
                        "priority": 4,
                    })

    except Exception as e:
        logger.warning("nudge_generation_error", error=str(e))
    finally:
        db.close()

    # Sort by priority
    nudges.sort(key=lambda n: n.get("priority", 99))
    return nudges


_nudge_cache: dict = {}
_CACHE_TTL = 300  # 5 minutes


def _cache_key(tenant_id: UUID, route: Optional[str]) -> str:
    route_hash = hashlib.md5((route or "").encode()).hexdigest()[:8]
    return f"copilot:nudge:{tenant_id}:{route_hash}"


@router.get("/nudge-context")
def get_nudge_context(route: Optional[str] = Query(None)):
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
