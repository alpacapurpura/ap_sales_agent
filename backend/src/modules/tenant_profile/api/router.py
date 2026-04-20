"""FastAPI router for the tenant_profile bounded context.

Mounts at ``/api/v1/tenant/profile`` (registered in ``main.py``).

Endpoints:
  GET  /api/v1/tenant/profile  — current profile for the authenticated tenant.
  PATCH /api/v1/tenant/profile — update business_types.

Error contract (§3.3 of CONTRACT.md):
  400 invalid_business_types — length / duplicate / unknown-slug violations.
  409 rate_limited           — attempted change within 30-day window.
  403 forbidden              — missing X-Tenant-ID header.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session  # noqa: TC002 — FastAPI needs runtime type for Annotated Depends

from src.core.database import get_db
from src.modules.tenant_profile.api.dtos import (
    TenantProfileResponse,
    UpdateTenantProfileRequest,
    parse_business_types_request,
    profile_to_response,
)
from src.modules.tenant_profile.application.services.tenant_profile_service import (
    TenantProfileService,
)
from src.modules.tenant_profile.domain.exceptions import (
    BusinessTypesChangeRateLimitedError,
)
from src.modules.tenant_profile.infrastructure.repositories.tenant_profile_repository import (
    SqlTenantProfileRepository,
)

logger = structlog.get_logger()

router = APIRouter()


def _get_service(db: Annotated[Session, Depends(get_db)]) -> TenantProfileService:
    """FastAPI dependency: build service with a scoped repository."""
    repo = SqlTenantProfileRepository(db)
    return TenantProfileService(repo)


def _require_tenant_id(
    x_tenant_id: Annotated[str | None, Header(alias="X-Tenant-ID")] = None,
) -> UUID:
    """Require and parse the ``X-Tenant-ID`` header.

    Returns:
        The parsed UUID.

    Raises:
        HTTPException 403: If the header is absent or not a valid UUID.
    """
    if not x_tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "X-Tenant-ID header is required"},
        )
    try:
        return UUID(x_tenant_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "X-Tenant-ID must be a valid UUID"},
        ) from exc


@router.get(
    "",
    response_model=TenantProfileResponse,
    summary="Get current tenant profile",
    description="Returns the operational classification for the authenticated tenant.",
)
def get_tenant_profile(
    tenant_id: Annotated[UUID, Depends(_require_tenant_id)],
    service: Annotated[TenantProfileService, Depends(_get_service)],
) -> TenantProfileResponse:
    """Return the current tenant profile.

    If the tenant has never completed onboarding, returns a profile with
    ``is_complete=False`` and empty ``business_types``.
    """
    profile = service.get_profile(tenant_id)
    logger.info(
        "tenant_profile_read",
        tenant_id=str(tenant_id),
        is_complete=profile.is_complete,
    )
    return profile_to_response(profile)


@router.patch(
    "",
    response_model=TenantProfileResponse,
    summary="Update tenant business_types",
    description=(
        "Declare or change the tenant's business_types. "
        "Rate-limited: max one change every 30 days after first declaration."
    ),
)
def update_tenant_profile(
    request: UpdateTenantProfileRequest,
    tenant_id: Annotated[UUID, Depends(_require_tenant_id)],
    service: Annotated[TenantProfileService, Depends(_get_service)],
) -> TenantProfileResponse:
    """Update the tenant's business_types.

    Raises 400 for invalid slugs, duplicate values, or wrong count.
    Raises 409 when the request is within the 30-day rate-limit window.
    """
    try:
        new_types = parse_business_types_request(request.business_types)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_business_types", "message": str(exc)},
        ) from exc

    try:
        profile = service.update_business_types(tenant_id, new_types)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_business_types", "message": str(exc)},
        ) from exc
    except BusinessTypesChangeRateLimitedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "rate_limited",
                "message": str(exc),
                "next_allowed_change_at": exc.next_allowed_at.isoformat(),
            },
        ) from exc

    return profile_to_response(profile)
