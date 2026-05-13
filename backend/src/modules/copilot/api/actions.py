"""Copilot actions API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from luana_core_brand_studio.api.dto.extraction import ExtractRequest
from luana_core_brand_studio.domain.identity import BrandVisuals
from luana_core_copilot.api.dto import BrandExtractResponse
from luana_core_copilot.application.services.brand_ai_actions_service import (
    CopilotBrandAIActionsService,
)
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/brand/extract", response_model=BrandExtractResponse)
async def extract_brand_data(
    request: ExtractRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BrandVisuals:
    """Extract brand data."""
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant.",
        )

    service = CopilotBrandAIActionsService(db, current_user.tenant_id)
    try:
        data = await service.extract_brand_identity(request.url, request.type)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Internal extraction error: {error!s}",
        ) from error

    if not data:
        raise HTTPException(
            status_code=422,
            detail="Extraction failed. Could not find relevant data on the page.",
        )

    return data
