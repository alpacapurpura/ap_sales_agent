from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from src.api.dependencies import get_db, get_current_tenant_id
from src.services.db.repositories.gallery_repository import GalleryRepository
from src.services.db.models.gallery import GalleryImage
from src.services.image_analysis_service import ImageAnalysisService
from src.services.database import SessionLocal
from uuid import UUID
import shutil
import os
import uuid
from pathlib import Path
import structlog

logger = structlog.get_logger()
router = APIRouter()
image_service = ImageAnalysisService()

BASE_UPLOAD_DIR = Path("static")

async def process_image_background(image_id: UUID, tenant_id: UUID, file_path: str, user_desc: str):
    logger.info("starting_image_analysis", image_id=str(image_id))
    db = SessionLocal()
    try:
        repo = GalleryRepository(db)
        image = repo.get_by_id(image_id, tenant_id)
        if not image:
            logger.error("image_not_found_background", image_id=str(image_id))
            return

        analysis = await image_service.analyze(file_path, user_context=user_desc)
        
        image.ai_description = analysis.get("description", "No description generated.")
        image.ai_colors = analysis.get("colors", [])
        image.status = "completed"
        
        repo.update(image)
        logger.info("image_analysis_completed", image_id=str(image_id))
        
    except Exception as e:
        logger.error("background_task_failed", error=str(e))
        # Try to set error status
        try:
            image.status = "failed"
            image.error_message = str(e)
            repo.update(image)
        except:
            pass
    finally:
        db.close()

@router.post("/upload", response_model=None)
async def upload_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    try:
        tenant_uuid = UUID(tenant_id)
        file_ext = file.filename.split(".")[-1]
        
        # New structure: static/{tenant_id}/brand/gallery
        gallery_dir = BASE_UPLOAD_DIR / tenant_id / "brand" / "gallery"
        gallery_dir.mkdir(parents=True, exist_ok=True)
        
        new_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = gallery_dir / new_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        public_url = f"/static/{tenant_id}/brand/gallery/{new_filename}"
        
        new_image = GalleryImage(
            tenant_id=tenant_uuid,
            filename=new_filename,
            file_path=str(file_path.absolute()),
            public_url=public_url,
            user_description=description,
            status="processing"
        )
        
        repo = GalleryRepository(db)
        saved_image = repo.create(new_image)
        
        background_tasks.add_task(
            process_image_background, 
            saved_image.id, 
            tenant_uuid, 
            str(file_path.absolute()), 
            description
        )
        
        return saved_image
    except Exception as e:
        logger.error("upload_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def list_images(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    repo = GalleryRepository(db)
    return repo.get_all_by_tenant(UUID(tenant_id))

@router.delete("/{image_id}")
def delete_image(
    image_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
):
    repo = GalleryRepository(db)
    image_uuid = UUID(image_id)
    tenant_uuid = UUID(tenant_id)
    
    image = repo.get_by_id(image_uuid, tenant_uuid)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
        
    # Delete file
    try:
        os.remove(image.file_path)
    except OSError:
        pass # File might be missing
        
    repo.delete(image_uuid, tenant_uuid)
    return {"status": "deleted"}
