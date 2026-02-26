from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from src.shared.infrastructure.db.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.gallery.application.gallery_service import GalleryService
from src.modules.gallery.domain.entity import GalleryImage
from uuid import UUID
from typing import List, Optional
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.post("/upload", response_model=GalleryImage)
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: str = Form(""),
    offer_id: str = Form(...), # Require offer_id
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    try:
        service = GalleryService(db)
        return service.upload_image(
            tenant_id=user.tenant_id,
            file_obj=file.file,
            filename=file.filename,
            description=description,
            background_tasks=background_tasks,
            offer_id=UUID(offer_id)
        )
    except Exception as e:
        logger.error("upload_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[GalleryImage])
def list_images(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = GalleryService(db)
    return service.list_images(tenant_id=user.tenant_id)

@router.delete("/{image_id}")
def delete_image(
    image_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    service = GalleryService(db)
    success = service.delete_image(tenant_id=user.tenant_id, image_id=UUID(image_id))
    
    if not success:
        raise HTTPException(status_code=404, detail="Image not found")
        
    return {"status": "deleted"}
