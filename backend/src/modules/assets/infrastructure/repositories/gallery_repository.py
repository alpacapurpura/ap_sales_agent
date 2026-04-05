from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.assets.domain.entity import GalleryImage
from src.modules.assets.infrastructure.models.gallery_model import GalleryImageModel


class GalleryRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, model: GalleryImageModel) -> GalleryImage:
        return GalleryImage(
            id=model.id,
            tenant_id=model.tenant_id,
            offer_id=model.offer_id,
            filename=model.filename,
            file_path=model.file_path,
            public_url=model.public_url,
            user_description=model.user_description,
            ai_description=model.ai_description,
            ai_colors=model.ai_colors or [],
            status=model.status,
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: GalleryImage) -> GalleryImageModel:
        return GalleryImageModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            offer_id=entity.offer_id,
            filename=entity.filename,
            file_path=entity.file_path,
            public_url=entity.public_url,
            user_description=entity.user_description,
            ai_description=entity.ai_description,
            ai_colors=entity.ai_colors,
            status=entity.status,
            error_message=entity.error_message,
        )

    def create(self, entity: GalleryImage) -> GalleryImage:
        model = self._to_model(entity)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, image_id: UUID) -> GalleryImage | None:
        stmt = select(GalleryImageModel).where(
            GalleryImageModel.id == image_id,
            GalleryImageModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalars().first()
        if model:
            return self._to_domain(model)
        return None

    def list_by_offer(self, offer_id: UUID) -> list[GalleryImage]:
        stmt = select(GalleryImageModel).where(
            GalleryImageModel.offer_id == offer_id,
            GalleryImageModel.deleted_at.is_(None),
        )
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def list_by_tenant(self, tenant_id: UUID) -> list[GalleryImage]:
        stmt = select(GalleryImageModel).where(
            GalleryImageModel.tenant_id == tenant_id,
            GalleryImageModel.deleted_at.is_(None),
        )
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def delete(self, image_id: UUID) -> bool:
        stmt = select(GalleryImageModel).where(
            GalleryImageModel.id == image_id,
            GalleryImageModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalars().first()
        if model:
            model.deleted_at = datetime.utcnow()
            self.db.flush()
            self.db.commit()
            return True
        return False
