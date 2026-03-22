from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException, Query
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.assets.application.assets_service import AssetsService
from src.modules.assets.domain.schemas import AssetDto
from uuid import UUID
from typing import List, Optional
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.post("/upload", response_model=AssetDto)
async def upload_asset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    offer_id: Optional[str] = Form(None), # Optional now
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
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
            offer_id=offer_uuid
        )
    except Exception as e:
        logger.error("upload_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[AssetDto])
def list_assets(
    type: Optional[str] = Query(None, description="Filter by asset type (IMAGE, VIDEO, etc)"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = AssetsService(db)
    return service.list_assets(tenant_id=user.tenant_id, asset_type=type)

@router.delete("/{asset_id}")
def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = AssetsService(db)
    success = service.delete_asset(tenant_id=user.tenant_id, asset_id=UUID(asset_id))
    
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    return {"status": "deleted"}
