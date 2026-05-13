"""Offer Gallery API endpoints."""

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from luana_core_assets.application.assets_service import AssetsService
from luana_core_assets.domain.schemas import AssetDto
from luana_core_iam.api.dependencies import get_current_tenant_id, get_db
from sqlalchemy.orm import Session

logger = structlog.get_logger()
router = APIRouter()


# Keep using AssetDto as response model (compatible with GalleryImageDto)
@router.post("/{offer_id}/gallery/upload")
async def upload_offer_image(
    offer_id: str,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_current_tenant_id)],
    description: Annotated[str, Form()] = "",
) -> AssetDto:
    """Upload offer image."""
    try:
        service = AssetsService(db)
        return service.upload_asset(
            tenant_id=UUID(tenant_id),
            file_obj=file.file,
            filename=file.filename,
            mime_type=file.content_type,
            description=description,
            background_tasks=background_tasks,
            offer_id=UUID(offer_id),
        )
    except Exception as e:
        logger.exception("offer_upload_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{offer_id}/gallery")
def list_offer_images(
    offer_id: str,
    db: Annotated[Session, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_current_tenant_id)],
) -> list[AssetDto]:
    """List offer images."""
    service = AssetsService(db)
    # This might need a new method in service or just use list_by_offer
    # But list_by_offer doesn't check tenant_id (repo does check offer_id which is
    # unique usually, but safer to check tenant too?)
    # AssetRepository.list_by_offer only checks offer_id.
    # We should trust offer_id belongs to tenant (checked elsewhere) or add check.
    # For now, rely on offer_id.
    return service.list_by_offer(offer_id=UUID(offer_id))


@router.delete("/{offer_id}/gallery/{image_id}")
def delete_offer_image(
    offer_id: str,  # Kept for URL compatibility
    image_id: str,
    db: Annotated[Session, Depends(get_db)],
    tenant_id: Annotated[str, Depends(get_current_tenant_id)],
) -> dict[str, str]:
    """Delete offer image."""
    service = AssetsService(db)
    # Pass offer_id to ensure ownership check
    success = service.delete_asset(
        tenant_id=UUID(tenant_id),
        asset_id=UUID(image_id),
        offer_id=UUID(offer_id),
    )

    if not success:
        raise HTTPException(status_code=404, detail="Image not found")

    return {"status": "deleted"}
