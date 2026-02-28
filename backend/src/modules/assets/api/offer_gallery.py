from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from src.modules.iam.api.dependencies import get_db, get_current_tenant_id
from src.modules.gallery.application.gallery_service import GalleryService
from src.modules.gallery.domain.schemas import GalleryImageDto
from uuid import UUID
import structlog
from typing import List

logger = structlog.get_logger()
router = APIRouter()

@router.post("/{offer_id}/gallery/upload", response_model=GalleryImageDto)
async def upload_offer_image(
    offer_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    try:
        service = GalleryService(db)
        return service.upload_image(
            tenant_id=UUID(tenant_id),
            file_obj=file.file,
            filename=file.filename,
            description=description,
            background_tasks=background_tasks,
            offer_id=UUID(offer_id)
        )
    except Exception as e:
        logger.error("offer_upload_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{offer_id}/gallery", response_model=List[GalleryImageDto])
def list_offer_images(
    offer_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    service = GalleryService(db)
    return service.list_images(tenant_id=UUID(tenant_id), offer_id=UUID(offer_id))

@router.delete("/{offer_id}/gallery/{image_id}")
def delete_offer_image(
    offer_id: str, # Kept for URL compatibility, but not strictly needed by service
    image_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    service = GalleryService(db)
    success = service.delete_image(tenant_id=UUID(tenant_id), image_id=UUID(image_id))
    
    if not success:
        raise HTTPException(status_code=404, detail="Image not found")
        
    return {"status": "deleted"}
