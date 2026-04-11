"""Offer asset service.

CRUD + upload/generate flows for the Assets tab on the offer page.

AI generation is a stub — ``generate_asset`` simply writes a row with
``source=ai`` and ``status=processing`` and returns immediately. The real
generation pipeline (flyer/video renderers) is out of scope for the
header refactor; a worker will consume these rows once it lands.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any

import structlog

from src.modules.offer.domain.assets import OfferAsset
from src.modules.offer.domain.enums import AssetSource, AssetStatus, AssetType
from src.modules.offer.domain.events import OfferAssetCreated, OfferAssetDeleted
from src.modules.offer.domain.exceptions import AssetNotFoundError
from src.shared.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from uuid import UUID

    from src.modules.offer.application.ports import (
        IFileStoragePort,
        IOfferAssetRepository,
    )


logger = structlog.get_logger(__name__)


_DEFAULT_MIME_BY_TYPE: dict[AssetType, str] = {
    AssetType.FLYER: "image/png",
    AssetType.IMAGE: "image/png",
    AssetType.VIDEO: "video/mp4",
    AssetType.CAROUSEL: "application/json",
    AssetType.DOCUMENT: "application/pdf",
}


class OfferAssetService:
    def __init__(
        self,
        *,
        asset_repo: IOfferAssetRepository,
        file_storage: IFileStoragePort,
        event_bus: object | None = None,
    ) -> None:
        self._repo = asset_repo
        self._storage = file_storage
        self._events = event_bus

    # --------------------------------------------------------------- list
    def list_assets(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        search: str | None = None,
        type: AssetType | None = None,
        source: AssetSource | None = None,
        sort: str = "created_desc",
        limit: int = 24,
        offset: int = 0,
    ) -> tuple[list[OfferAsset], int]:
        return self._repo.list(
            tenant_id,
            offer_id,
            search=search,
            type=type,
            source=source,
            sort=sort,
            limit=limit,
            offset=offset,
        )

    # --------------------------------------------------------------- get
    def get_asset(
        self, *, tenant_id: UUID, offer_id: UUID, asset_id: UUID
    ) -> OfferAsset:
        asset = self._repo.get_by_id(tenant_id, offer_id, asset_id)
        if asset is None:
            raise AssetNotFoundError(asset_id)
        return asset

    # -------------------------------------------------------------- upload
    def upload_asset(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        file_bytes: bytes,
        filename: str,
        type: AssetType,
        mime_type: str | None = None,
    ) -> OfferAsset:
        mime = mime_type or _DEFAULT_MIME_BY_TYPE.get(type, "application/octet-stream")
        stream: BytesIO = BytesIO(file_bytes)
        folder = f"offers/{offer_id}/assets"
        file_url, size_bytes = self._storage.upload(
            tenant_id=tenant_id,
            folder=folder,
            filename=filename,
            content=stream,
            mime_type=mime,
        )
        asset = OfferAsset(
            tenant_id=tenant_id,
            offer_id=offer_id,
            name=filename,
            type=type,
            source=AssetSource.EXTERNAL,
            status=AssetStatus.READY,
            file_url=file_url,
            mime_type=mime,
            size_bytes=size_bytes,
            editable_in_puck=False,
        )
        created = self._repo.create(asset)
        self._emit_created(created)
        logger.info(
            "offer_asset_uploaded",
            asset_id=str(created.id),
            offer_id=str(offer_id),
            tenant_id=str(tenant_id),
            type=type.value,
        )
        return created

    # ------------------------------------------------------------ generate
    def generate_asset(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        type: AssetType,
        prompt_params: dict[str, Any] | None = None,
        name: str | None = None,
    ) -> OfferAsset:
        """Stub: enqueue an AI-generated asset row. Actual generation is
        handled by a downstream worker — this service returns immediately."""
        asset = OfferAsset(
            tenant_id=tenant_id,
            offer_id=offer_id,
            name=name or f"AI {type.value}",
            type=type,
            source=AssetSource.AI,
            status=AssetStatus.PROCESSING,
            prompt_params=prompt_params,
            editable_in_puck=True,
        )
        created = self._repo.create(asset)
        self._emit_created(created)
        logger.info(
            "offer_asset_generate_queued",
            asset_id=str(created.id),
            offer_id=str(offer_id),
            tenant_id=str(tenant_id),
            type=type.value,
        )
        return created

    # --------------------------------------------------------------- update
    def update_asset(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        asset_id: UUID,
        fields: dict[str, Any],
    ) -> OfferAsset:
        asset = self._repo.get_by_id(tenant_id, offer_id, asset_id)
        if asset is None:
            raise AssetNotFoundError(asset_id)
        # Whitelist the mutable fields — status and provenance remain
        # controlled by the service itself.
        _MUTABLE = {"name", "metadata", "thumbnail_url"}
        patch = {k: v for k, v in fields.items() if k in _MUTABLE}
        if not patch:
            return asset
        current = asset.model_dump()
        current.update(patch)
        updated = OfferAsset.model_validate(current)
        return self._repo.update(updated)

    # --------------------------------------------------------------- delete
    def delete_asset(self, *, tenant_id: UUID, offer_id: UUID, asset_id: UUID) -> None:
        ok = self._repo.soft_delete(tenant_id, offer_id, asset_id)
        if not ok:
            raise AssetNotFoundError(asset_id)
        self._emit_deleted(tenant_id=tenant_id, offer_id=offer_id, asset_id=asset_id)
        logger.info(
            "offer_asset_deleted",
            asset_id=str(asset_id),
            offer_id=str(offer_id),
            tenant_id=str(tenant_id),
        )

    # ---------------------------------------------------------- download_url
    def get_download_url(
        self, *, tenant_id: UUID, offer_id: UUID, asset_id: UUID
    ) -> str:
        asset = self._repo.get_by_id(tenant_id, offer_id, asset_id)
        if asset is None:
            raise AssetNotFoundError(asset_id)
        if not asset.file_url:
            raise AssetNotFoundError(asset_id)
        return self._storage.get_signed_url(asset.file_url)

    # -------------------------------------------------------------- events
    def _emit_created(self, asset: OfferAsset) -> None:
        if self._events is None:
            return
        event = OfferAssetCreated(
            tenant_id=asset.tenant_id,
            occurred_at=utc_now(),
            offer_id=asset.offer_id,
            asset_id=asset.id,
            type=asset.type,
            source=asset.source.value,
        )
        try:
            self._events.publish(event)
        except Exception:
            logger.warning("offer_asset_event_publish_failed", asset_id=str(asset.id))

    def _emit_deleted(self, *, tenant_id: UUID, offer_id: UUID, asset_id: UUID) -> None:
        if self._events is None:
            return
        event = OfferAssetDeleted(
            tenant_id=tenant_id,
            occurred_at=utc_now(),
            offer_id=offer_id,
            asset_id=asset_id,
        )
        try:
            self._events.publish(event)
        except Exception:
            logger.warning("offer_asset_event_publish_failed", asset_id=str(asset_id))


__all__ = ["OfferAssetService"]
