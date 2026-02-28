from sqlalchemy.orm import Session
from fastapi import UploadFile, BackgroundTasks
from uuid import UUID
import os
import shutil
from typing import List, Optional
from src.modules.gallery.domain.entity import GalleryImage
from src.modules.gallery.infrastructure.repositories.gallery_repository import GalleryRepository
from src.core.config import settings # Ensure this exists or use relative import

class GalleryService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = GalleryRepository(db)
        # TODO: Move to config
        self.upload_dir = "static/uploads" 
        os.makedirs(self.upload_dir, exist_ok=True)

    def upload_image(
        self, 
        tenant_id: UUID, 
        file_obj, 
        filename: str, 
        description: str, 
        background_tasks: BackgroundTasks, 
        offer_id: Optional[UUID] = None
    ) -> GalleryImage:
        import uuid
        image_id = uuid.uuid4()
        
        # 1. Save File
        # Structure: static/uploads/{tenant_id}/{offer_id}/{filename}
        # For simplicity: static/uploads/{filename}_{uuid}
        safe_filename = f"{image_id}_{filename}"
        file_path = os.path.join(self.upload_dir, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
            
        public_url = f"/static/uploads/{safe_filename}" # Assuming static mount
        
        # 2. Create Entity
        # If offer_id is None, it might be a general gallery image or temp
        # For now, require offer_id or use a placeholder if allowed by domain
        if not offer_id:
             # This might fail if DB constraint is strict. 
             # Check GalleryImageModel.offer_id nullable? It is nullable=False in model above.
             # So we MUST provide offer_id. If not provided, maybe use a default or error.
             # Let's assume frontend sends it, or we create a "General" offer for the tenant.
             raise ValueError("Offer ID is required for gallery upload")

        image = GalleryImage(
            id=image_id,
            tenant_id=tenant_id,
            offer_id=offer_id,
            filename=filename,
            file_path=file_path,
            public_url=public_url,
            user_description=description,
            status="processing"
        )
        
        created_image = self.repository.create(image)
        
        # 3. Trigger AI Analysis (Background)
        # background_tasks.add_task(self.analyze_image, created_image.id)
        
        return created_image

    def list_images(self, tenant_id: UUID) -> List[GalleryImage]:
        return self.repository.list_by_tenant(tenant_id)

    def delete_image(self, tenant_id: UUID, image_id: UUID) -> bool:
        image = self.repository.get_by_id(image_id)
        if not image or str(image.tenant_id) != str(tenant_id):
            return False
            
        # Delete file
        if os.path.exists(image.file_path):
            os.remove(image.file_path)
            
        return self.repository.delete(image_id)
