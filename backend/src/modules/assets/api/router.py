"""Router API endpoints."""

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
    Query,
    UploadFile,
)
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.assets.application.assets_service import AssetsService
from src.modules.assets.domain.enums import DEFAULT_SCOPE_FOR_PURPOSE
from src.modules.assets.domain.schemas import AssetDto, PromoteAssetRequest
from src.modules.assets.infrastructure.repositories.asset_link_repository import (
    AssetLinkRepository,
)
from src.modules.assets.infrastructure.repositories.asset_repository import (
    AssetRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

logger = structlog.get_logger()
router = APIRouter()


@router.post("/upload")
async def upload_asset(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    description: Annotated[str | None, Form()] = None,
    offer_id: Annotated[str | None, Form()] = None,  # Optional now
) -> AssetDto:
    """Upload asset."""
    try:
        service = AssetsService(db)
        # Convert offer_id to UUID if provided
        offer_uuid = UUID(offer_id) if offer_id else None

        return service.upload_asset(
            tenant_id=user.tenant_id,
            file_obj=file.file,
            filename=file.filename,
            mime_type=file.content_type,
            description=description,
            background_tasks=background_tasks,
            offer_id=offer_uuid,
        )
    except Exception as e:
        logger.exception("upload_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/")
def list_assets(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    type_: Annotated[str | None, Query(alias="type", description="Filter by asset type (IMAGE, VIDEO, etc)")] = None,
) -> list[AssetDto]:
    """List assets."""
    service = AssetsService(db)
    return service.list_assets(tenant_id=user.tenant_id, asset_type=type_)


@router.post("/{asset_id}/promote")
def promote_asset(
    asset_id: UUID,
    body: PromoteAssetRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AssetDto:
    """Promote an asset from ``ephemeral`` to ``library`` / ``deliverable``.

    Idempotent: promoting the same asset with the same payload re-uses
    the active link row. The DTO validator already rejects deliverable
    purposes without a link target, so the endpoint itself stays thin.
    """
    if not user.tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID requerido")

    repo = AssetRepository(db)
    asset = repo.get_by_id(asset_id, tenant_id=user.tenant_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset no encontrado")

    target_scope = DEFAULT_SCOPE_FOR_PURPOSE[body.purpose]

    updated = repo.update_partial(
        asset_id,
        tenant_id=user.tenant_id,
        scope=target_scope.value,
        purpose=body.purpose.value,
        expires_at=None,  # promoted assets never auto-expire
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Asset no encontrado")

    # Deliverable purposes always carry a link target (enforced by the DTO).
    if body.entity_type and body.entity_id and body.role:
        link_repo = AssetLinkRepository(db)
        link_repo.create(
            tenant_id=user.tenant_id,
            asset_id=asset_id,
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            role=body.role,
        )

    db.commit()
    logger.info(
        "asset_promoted",
        asset_id=str(asset_id),
        scope=target_scope.value,
        purpose=body.purpose.value,
        tenant_id=str(user.tenant_id),
    )
    return updated


@router.delete("/{asset_id}")
def delete_asset(
    asset_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, str]:
    """Delete asset."""
    service = AssetsService(db)
    success = service.delete_asset(tenant_id=user.tenant_id, asset_id=UUID(asset_id))

    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")

    return {"status": "deleted"}
