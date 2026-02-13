from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from src.services.db.models.offer_gallery import OfferGalleryImage
from uuid import UUID

class OfferGalleryRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, image: OfferGalleryImage) -> OfferGalleryImage:
        self.session.add(image)
        self.session.commit()
        self.session.refresh(image)
        return image

    def get_all_by_offer(self, offer_id: UUID, tenant_id: UUID):
        result = self.session.execute(
            select(OfferGalleryImage)
            .where(OfferGalleryImage.offer_id == offer_id, OfferGalleryImage.tenant_id == tenant_id)
            .order_by(OfferGalleryImage.created_at.desc())
        )
        return result.scalars().all()

    def get_by_id(self, image_id: UUID, tenant_id: UUID):
        result = self.session.execute(
            select(OfferGalleryImage).where(OfferGalleryImage.id == image_id, OfferGalleryImage.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    def delete(self, image_id: UUID, tenant_id: UUID):
        self.session.execute(
            delete(OfferGalleryImage).where(OfferGalleryImage.id == image_id, OfferGalleryImage.tenant_id == tenant_id)
        )
        self.session.commit()

    def update(self, image: OfferGalleryImage):
        self.session.commit()
        self.session.refresh(image)
        return image
