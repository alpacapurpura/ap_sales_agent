import shutil
from pathlib import Path
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from src.core.config import settings  # Ensure this exists or use relative import
from src.modules.assets.domain.entity import GalleryImage
from src.modules.assets.infrastructure.repositories.gallery_repository import (
    GalleryRepository,
)


class GalleryService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = GalleryRepository(db)
        self.upload_dir = settings.UPLOAD_DIR
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)

    def upload_image(
        self,
        tenant_id: UUID,
        file_obj,
        filename: str,
        description: str,
        background_tasks: BackgroundTasks,
        offer_id: UUID | None = None,
    ) -> GalleryImage:
        import uuid

        image_id = uuid.uuid4()

        # 1. Save File
        # Saves to static/uploads/{uuid}_{filename}
        safe_filename = f"{image_id}_{filename}"
        file_path = str(Path(self.upload_dir) / safe_filename)

        with Path(file_path).open("wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)

        public_url = f"/static/uploads/{safe_filename}"  # Assuming static mount

        # 2. Create Entity
        # If offer_id is None, it might be a general gallery image or temp
        # For now, require offer_id or use a placeholder if allowed by domain
        if not offer_id:
            # This might fail if DB constraint is strict.
            # Check GalleryImageModel.offer_id nullable? It is nullable=False in model above.
            # So we MUST provide offer_id. If not provided, maybe use a default or error.
            # Let's assume frontend sends it, or we create a "General" offer for the tenant.
            msg = "Offer ID is required for gallery upload"
            raise ValueError(msg)

        image = GalleryImage(
            id=image_id,
            tenant_id=tenant_id,
            offer_id=offer_id,
            filename=filename,
            file_path=file_path,
            public_url=public_url,
            user_description=description,
            status="processing",
        )

        created_image = self.repository.create(image)

        return created_image

    def list_images(self, tenant_id: UUID) -> list[GalleryImage]:
        return self.repository.list_by_tenant(tenant_id)

    def delete_image(
        self,
        tenant_id: UUID,
        image_id: UUID,
        offer_id: UUID | None = None,
    ) -> bool:
        image = self.repository.get_by_id(image_id, tenant_id=tenant_id)
        if not image or str(image.tenant_id) != str(tenant_id):
            return False

        if offer_id and str(image.offer_id) != str(offer_id):
            return False

        # Delete file
        fp = Path(image.file_path)
        if fp.exists():
            fp.unlink()

        return self.repository.delete(image_id)
