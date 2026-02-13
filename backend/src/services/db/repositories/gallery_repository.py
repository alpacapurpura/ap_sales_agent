from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from src.services.db.models.gallery import GalleryImage
from uuid import UUID

class GalleryRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, image: GalleryImage) -> GalleryImage:
        self.session.add(image)
        self.session.commit()
        self.session.refresh(image)
        return image

    def get_all_by_tenant(self, tenant_id: UUID):
        result = self.session.execute(
            select(GalleryImage).where(GalleryImage.tenant_id == tenant_id).order_by(GalleryImage.created_at.desc())
        )
        return result.scalars().all()

    def get_by_id(self, image_id: UUID, tenant_id: UUID):
        result = self.session.execute(
            select(GalleryImage).where(GalleryImage.id == image_id, GalleryImage.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    def delete(self, image_id: UUID, tenant_id: UUID):
        self.session.execute(
            delete(GalleryImage).where(GalleryImage.id == image_id, GalleryImage.tenant_id == tenant_id)
        )
        self.session.commit()

    def update(self, image: GalleryImage):
        self.session.commit()
        self.session.refresh(image)
        return image
