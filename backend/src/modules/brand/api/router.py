"""Brand API router.

Note on ``business_types``:
  The field was removed from ``BrandIdentity`` in Sprint 2026-04-20 and moved
  to the ``tenant_profile`` bounded context. PATCH /api/v1/brand/settings now
  actively rejects payloads containing ``identity.business_types`` with 400 to
  surface the migration to frontend callers early (§3.4 of tenant-profile
  CONTRACT.md). Read/write business_types via PATCH /api/v1/tenant/profile.
"""

from __future__ import annotations

from typing import Annotated, Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.brand.domain import BrandSettings
from src.modules.brand.infrastructure.repositories.brand_repository import (
    BrandRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

logger = structlog.get_logger()

router = APIRouter()


def _reject_business_types_in_payload(raw: dict[str, Any]) -> None:
    """Raise 400 if the raw payload contains ``identity.business_types``.

    Called before Pydantic validation because Pydantic's ``extra="allow"``
    would silently accept and then discard the key — the caller would not
    receive feedback that they are using a deprecated code path.
    """
    identity = raw.get("identity")
    if isinstance(identity, dict) and "business_types" in identity:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "field_moved",
                "message": (
                    "business_types must be updated via "
                    "PATCH /api/v1/tenant/profile — it is no longer part of brand settings."
                ),
            },
        )


@router.get("", response_model=BrandSettings)
async def get_brand_settings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BrandSettings:
    """Get Global Brand Settings for the user's tenant.

    Note: ``identity.business_types`` is NOT returned — it was moved to
    ``GET /api/v1/tenant/profile``.
    """
    if not current_user.tenant_id:
        logger.error(
            "get_brand_settings_error",
            error="no_tenant_id",
            user_id=str(current_user.id),
        )
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant",
        )

    repo = BrandRepository(db)
    settings = repo.get_settings(current_user.tenant_id)

    # Log what we're returning
    settings_dict = settings.model_dump(mode="json")
    logger.info(
        "get_brand_settings_response",
        tenant_id=str(current_user.tenant_id),
        has_identity=bool((settings_dict.get("identity") or {}).get("brand_name")),
        has_story=bool((settings_dict.get("story") or {}).get("origin_story")),
        has_strategy=bool(
            (settings_dict.get("strategy") or {}).get("value_proposition"),
        ),
        team_count=len(settings_dict.get("team") or []),
        testimonials_count=len(settings_dict.get("testimonials") or []),
        response_keys=list(settings_dict.keys()),
    )

    # Validation/Defaulting handled by Pydantic
    return settings


@router.patch("", response_model=BrandSettings)
async def update_brand_settings(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BrandSettings:
    """Update Global Brand Settings for the user's tenant.

    Rejects payloads that include ``identity.business_types`` with a 400 error
    and a hint pointing to the new endpoint.
    """
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant",
        )

    raw: dict[str, Any] = await request.json()
    _reject_business_types_in_payload(raw)

    # Re-parse into BrandSettings after rejection check.
    settings = BrandSettings.model_validate(raw)

    repo = BrandRepository(db)

    # We might want to merge with existing settings here if the frontend sends partial updates
    # But for now assuming full replacement of sub-objects as per Pydantic behavior
    updated_settings = repo.save_settings(current_user.tenant_id, settings)

    return updated_settings
