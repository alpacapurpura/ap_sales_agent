"""Repository for offer_assets CRUD operations.

Implements `IOfferAssetRepository` from `offer.application.ports`. All
queries filter by `tenant_id` (multitenant isolation) and exclude
soft-deleted rows (`deleted_at IS NULL`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, or_, select

from src.modules.offer.application.ports import IOfferAssetRepository
from src.modules.offer.domain.assets import OfferAsset
from src.modules.offer.domain.enums import (
    AssetSource,
    AssetStatus,
    AssetType,
)
from src.modules.offer.infrastructure.models.offer_asset_model import OfferAssetModel
from src.shared.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


class OfferAssetRepository(IOfferAssetRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------ mapping

    @staticmethod
    def _to_domain(model: OfferAssetModel) -> OfferAsset:
        return OfferAsset(
            id=model.id,
            tenant_id=model.tenant_id,
            offer_id=model.offer_id,
            name=model.name,
            type=AssetType(model.type),
            source=AssetSource(model.source),
            status=AssetStatus(model.status),
            file_url=model.file_url,
            thumbnail_url=model.thumbnail_url,
            mime_type=model.mime_type,
            size_bytes=model.size_bytes,
            metadata=dict(model.metadata_json or {}),
            prompt_params=(dict(model.prompt_params) if model.prompt_params else None),
            editable_in_puck=bool(model.editable_in_puck),
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _apply_domain_to_model(model: OfferAssetModel, asset: OfferAsset) -> None:
        model.tenant_id = asset.tenant_id
        model.offer_id = asset.offer_id
        model.name = asset.name
        model.type = asset.type.value
        model.source = asset.source.value
        model.status = asset.status.value
        model.file_url = asset.file_url
        model.thumbnail_url = asset.thumbnail_url
        model.mime_type = asset.mime_type
        model.size_bytes = asset.size_bytes
        model.metadata_json = dict(asset.metadata or {})
        model.prompt_params = (
            dict(asset.prompt_params) if asset.prompt_params is not None else None
        )
        model.editable_in_puck = asset.editable_in_puck
        model.error_message = asset.error_message

    # ------------------------------------------------------------------ CRUD

    def create(self, asset: OfferAsset) -> OfferAsset:
        model = OfferAssetModel(id=asset.id)
        self._apply_domain_to_model(model, asset)
        self.db.add(model)
        self.db.flush()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        asset_id: UUID,
    ) -> OfferAsset | None:
        stmt = select(OfferAssetModel).where(
            OfferAssetModel.id == asset_id,
            OfferAssetModel.tenant_id == tenant_id,
            OfferAssetModel.offer_id == offer_id,
            OfferAssetModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def list(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        *,
        search: str | None = None,
        type_: AssetType | None = None,
        source: AssetSource | None = None,
        sort: str = "created_desc",
        limit: int = 24,
        offset: int = 0,
    ) -> tuple[list[OfferAsset], int]:
        base_filters = [
            OfferAssetModel.tenant_id == tenant_id,
            OfferAssetModel.offer_id == offer_id,
            OfferAssetModel.deleted_at.is_(None),
        ]
        if search:
            like = f"%{search}%"
            base_filters.append(
                or_(
                    OfferAssetModel.name.ilike(like),
                    OfferAssetModel.mime_type.ilike(like),
                ),
            )
        if type_ is not None:
            base_filters.append(OfferAssetModel.type == type_.value)
        if source is not None:
            base_filters.append(OfferAssetModel.source == source.value)

        count_stmt = select(func.count(OfferAssetModel.id)).where(*base_filters)
        total = int(self.db.execute(count_stmt).scalar() or 0)

        stmt = select(OfferAssetModel).where(*base_filters)
        if sort == "created_asc":
            stmt = stmt.order_by(OfferAssetModel.created_at.asc())
        elif sort == "name_asc":
            stmt = stmt.order_by(OfferAssetModel.name.asc())
        elif sort == "name_desc":
            stmt = stmt.order_by(OfferAssetModel.name.desc())
        else:  # "created_desc" default
            stmt = stmt.order_by(OfferAssetModel.created_at.desc())

        stmt = stmt.limit(limit).offset(offset)
        rows = self.db.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in rows], total

    def update(self, asset: OfferAsset) -> OfferAsset:
        stmt = select(OfferAssetModel).where(
            OfferAssetModel.id == asset.id,
            OfferAssetModel.tenant_id == asset.tenant_id,
            OfferAssetModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if model is None:
            msg = f"OfferAsset {asset.id} not found for update"
            raise ValueError(msg)
        self._apply_domain_to_model(model, asset)
        self.db.flush()
        self.db.refresh(model)
        return self._to_domain(model)

    def soft_delete(self, tenant_id: UUID, offer_id: UUID, asset_id: UUID) -> bool:
        stmt = select(OfferAssetModel).where(
            OfferAssetModel.id == asset_id,
            OfferAssetModel.tenant_id == tenant_id,
            OfferAssetModel.offer_id == offer_id,
            OfferAssetModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if model is None:
            return False
        model.deleted_at = utc_now()
        self.db.flush()
        return True

    def count_by_offer(self, tenant_id: UUID, offer_id: UUID) -> int:
        stmt = select(func.count(OfferAssetModel.id)).where(
            OfferAssetModel.tenant_id == tenant_id,
            OfferAssetModel.offer_id == offer_id,
            OfferAssetModel.deleted_at.is_(None),
        )
        return int(self.db.execute(stmt).scalar() or 0)
