"""Business Types Catalog endpoint.

Mounted at ``/api/v1/catalogs/business-types`` (registered in ``main.py``).

This endpoint was previously at ``GET /api/v1/brand/expert-business-types/catalog``.
It has been moved here because the catalog is cross-module domain metadata owned
by the platform (``shared/domain/expert_business_type.py``), not by the Brand Studio
bounded context.

The old URL serves a 301 redirect for two weeks (also registered in ``main.py``
for backward compatibility). After the deprecation window, delete the redirect.

Tenant-agnostic — identical response for all tenants. Highly cacheable: consumers
key their cache by the returned ``version`` and evict on bump.
"""

from __future__ import annotations

from fastapi import APIRouter
from luana_core_tenant_profile.api.dtos import (
    BusinessTypesCatalogResponse,
    _build_catalog_response,
)

router = APIRouter()

# Bump this when ``expert_business_type.py`` changes materially (new type,
# renamed label, description rewrite, new icon). Frontend caches by this version.
_CATALOG_VERSION = "2026-04-20"


@router.get(
    "",
    response_model=BusinessTypesCatalogResponse,
    summary="Expert business type catalog (public, cacheable)",
    description=(
        "Returns metadata for every ExpertBusinessType. "
        "Tenant-agnostic. Consumers key their cache by the returned ``version``."
    ),
)
def get_business_types_catalog() -> BusinessTypesCatalogResponse:
    """Return versioned metadata for all ExpertBusinessType values."""
    return _build_catalog_response(_CATALOG_VERSION)
