from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.assets.domain.entity import Asset
from src.modules.assets.infrastructure.models.asset_model import AssetModel


class AssetRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, model: AssetModel) -> Asset:
        return Asset(
            id=model.id,
            tenant_id=model.tenant_id,
            offer_id=model.offer_id,
            type=model.type,
            filename=model.filename,
            mime_type=model.mime_type,
            storage_provider=model.storage_provider,
            storage_path=model.storage_path,
            public_url=model.public_url,
            user_description=model.user_description,
            ai_metadata=model.ai_metadata or {},
            ai_description=model.ai_description,
            ai_colors=model.ai_colors or [],
            status=model.status,
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: Asset) -> AssetModel:
        return AssetModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            offer_id=entity.offer_id,
            type=entity.type,
            filename=entity.filename,
            mime_type=entity.mime_type,
            storage_provider=entity.storage_provider,
            storage_path=entity.storage_path,
            public_url=entity.public_url,
            user_description=entity.user_description,
            ai_metadata=entity.ai_metadata,
            ai_description=entity.ai_description,
            ai_colors=entity.ai_colors,
            status=entity.status,
            error_message=entity.error_message,
        )

    def create(self, entity: Asset) -> Asset:
        model = self._to_model(entity)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, asset_id: UUID) -> Asset | None:
        model = self.db.query(AssetModel).filter(AssetModel.id == asset_id).first()
        if model:
            return self._to_domain(model)
        return None

    def list_by_tenant(
        self, tenant_id: UUID, asset_type: str | None = None
    ) -> list[Asset]:
        query = self.db.query(AssetModel).filter(AssetModel.tenant_id == tenant_id)
        if asset_type:
            query = query.filter(AssetModel.type == asset_type)
        models = query.all()
        return [self._to_domain(m) for m in models]

    def list_by_offer(self, offer_id: UUID) -> list[Asset]:
        models = self.db.query(AssetModel).filter(AssetModel.offer_id == offer_id).all()
        return [self._to_domain(m) for m in models]

    def delete(self, asset_id: UUID) -> bool:
        model = self.db.query(AssetModel).filter(AssetModel.id == asset_id).first()
        if model:
            self.db.delete(model)
            self.db.commit()
            return True
        return False
