from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException
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


@router.get("", response_model=BrandSettings)
async def get_brand_settings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Get Global Brand Settings for the user's tenant.
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
    settings: BrandSettings,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Update Global Brand Settings for the user's tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant",
        )

    repo = BrandRepository(db)

    # We might want to merge with existing settings here if the frontend sends partial updates
    # But for now assuming full replacement of sub-objects as per Pydantic behavior
    updated_settings = repo.save_settings(current_user.tenant_id, settings)

    return updated_settings
