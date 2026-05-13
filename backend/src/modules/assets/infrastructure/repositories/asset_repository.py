"""Asset Repository implementation."""

from uuid import UUID

from luana_core_assets.domain.entity import Asset
from luana_core_assets.infrastructure.models.asset_model import AssetModel
from luana_core_platform.domain.datetime_utils import utc_now
from sqlalchemy import select
from sqlalchemy.orm import Session


class AssetRepository:
    """Concrete repository implementation for asset."""

    def __init__(self, db: Session) -> None:
        """Initialize AssetRepository."""
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
            scope=model.scope or "ephemeral",
            purpose=model.purpose or "context_extract",
            extracted_text=model.extracted_text,
            extracted_summary=model.extracted_summary,
            extracted_at=model.extracted_at,
            extraction_status=model.extraction_status or "pending",
            extraction_error=model.extraction_error,
            expires_at=model.expires_at,
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
            scope=entity.scope,
            purpose=entity.purpose,
            extracted_text=entity.extracted_text,
            extracted_summary=entity.extracted_summary,
            extracted_at=entity.extracted_at,
            extraction_status=entity.extraction_status,
            extraction_error=entity.extraction_error,
            expires_at=entity.expires_at,
        )

    def create(self, entity: Asset) -> Asset:
        """Handle create operation."""
        model = self._to_model(entity)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, asset_id: UUID, tenant_id: UUID) -> Asset | None:
        """Retrieve by id."""
        stmt = select(AssetModel).where(
            AssetModel.id == asset_id,
            AssetModel.tenant_id == tenant_id,
            AssetModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalars().first()
        if model:
            return self._to_domain(model)
        return None

    def list_by_tenant(
        self,
        tenant_id: UUID,
        asset_type: str | None = None,
    ) -> list[Asset]:
        """List by tenant."""
        stmt = select(AssetModel).where(
            AssetModel.tenant_id == tenant_id,
            AssetModel.deleted_at.is_(None),
        )
        if asset_type:
            stmt = stmt.where(AssetModel.type == asset_type)
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def list_by_offer(self, offer_id: UUID) -> list[Asset]:
        """List by offer."""
        stmt = select(AssetModel).where(
            AssetModel.offer_id == offer_id,
            AssetModel.deleted_at.is_(None),
        )
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def delete(self, asset_id: UUID) -> bool:
        """Handle delete operation."""
        stmt = select(AssetModel).where(
            AssetModel.id == asset_id,
            AssetModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalars().first()
        if model:
            model.deleted_at = utc_now()
            self.db.flush()
            self.db.commit()
            return True
        return False

    def update_partial(self, asset_id: UUID, tenant_id: UUID, **fields: object) -> Asset | None:
        """Apply a partial update on an asset owned by ``tenant_id``.

        Only whitelisted fields are updated — the whitelist mirrors columns
        whose mutation makes sense outside a full lifecycle event
        (extraction pipeline, scope promotion, description edit).
        """
        allowed = {
            "scope",
            "purpose",
            "extracted_text",
            "extracted_summary",
            "extracted_at",
            "extraction_status",
            "extraction_error",
            "expires_at",
            "status",
            "ai_description",
            "ai_metadata",
            "user_description",
            "error_message",
        }
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return self.get_by_id(asset_id, tenant_id)

        stmt = select(AssetModel).where(
            AssetModel.id == asset_id,
            AssetModel.tenant_id == tenant_id,
            AssetModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalars().first()
        if not model:
            return None
        for key, value in updates.items():
            setattr(model, key, value)
        self.db.flush()
        return self._to_domain(model)
