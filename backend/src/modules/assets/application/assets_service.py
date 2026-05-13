"""Assets Service for the assets module."""

import mimetypes
import uuid
from datetime import timedelta
from typing import BinaryIO
from uuid import UUID

import structlog
from fastapi import BackgroundTasks
from luana_core_assets.application.asset_extraction_service import (
    AssetExtractionService,
)
from luana_core_assets.application.asset_processor import AssetProcessor
from luana_core_assets.domain.entity import Asset
from luana_core_assets.domain.enums import (
    DEFAULT_SCOPE_FOR_PURPOSE,
    AssetPurpose,
    AssetScope,
    AssetStatus,
    AssetType,
    ExtractionStatus,
    StorageProvider,
)
from luana_core_assets.infrastructure.repositories.asset_repository import (
    AssetRepository,
)
from luana_core_assets.infrastructure.storage import get_storage_strategy
from luana_core_platform.core.config import settings
from luana_core_platform.domain.datetime_utils import utc_now
from sqlalchemy.orm import Session

logger = structlog.get_logger()


class AssetsService:
    """Manage assets operations."""

    def __init__(self, db: Session) -> None:
        """Initialize AssetsService."""
        self.db = db
        self.repository = AssetRepository(db)
        self.storage = get_storage_strategy()
        self.processor = AssetProcessor()

    def _detect_type(self, mime_type: str) -> AssetType:
        if mime_type.startswith("image/"):
            return AssetType.IMAGE
        if mime_type.startswith("video/"):
            return AssetType.VIDEO
        if mime_type.startswith("audio/"):
            return AssetType.AUDIO
        return AssetType.DOCUMENT

    def _get_storage_provider(self) -> StorageProvider:
        if settings.STORAGE_PROVIDER.upper() == "R2":
            return StorageProvider.R2
        return StorageProvider.LOCAL

    # Default TTL for ephemeral assets — 90 days aligns with conversation
    # retention (``CONVERSATION_RETENTION_DAYS`` in the copilot module).
    EPHEMERAL_TTL_DAYS = 90

    def upload_asset(
        self,
        tenant_id: UUID,
        file_obj: BinaryIO,
        filename: str,
        mime_type: str | None = None,
        description: str | None = None,
        offer_id: UUID | None = None,
        background_tasks: BackgroundTasks | None = None,
        *,
        scope: AssetScope | str | None = None,
        purpose: AssetPurpose | str | None = None,
    ) -> Asset:
        """Upload an asset and trigger the AI + text extraction pipelines.

        ``scope`` and ``purpose`` default to ``ephemeral`` + ``context_extract``
        (the copilot chat upload case). Module-specific endpoints can pass
        ``scope=library`` / ``purpose=brand_asset`` etc. to skip the ephemeral
        lifecycle for canonical uploads.
        """
        # 1. Detect MIME Type
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream"

        asset_type = self._detect_type(mime_type)

        # 2. Save File
        path_prefix = f"{tenant_id!s}/{asset_type.lower()}"
        storage_path, public_url = self.storage.save(file_obj, filename, path_prefix)

        # 3. Resolve scope + purpose + expiry
        resolved_purpose = AssetPurpose(str(purpose)) if purpose else AssetPurpose.CONTEXT_EXTRACT
        resolved_scope = AssetScope(str(scope)) if scope else DEFAULT_SCOPE_FOR_PURPOSE[resolved_purpose]
        expires_at = None
        if resolved_scope == AssetScope.EPHEMERAL:
            expires_at = utc_now() + timedelta(days=self.EPHEMERAL_TTL_DAYS)

        # 4. Create Entity
        asset_id = uuid.uuid4()
        asset = Asset(
            id=asset_id,
            tenant_id=tenant_id,
            offer_id=offer_id,
            type=asset_type,
            filename=filename,
            mime_type=mime_type,
            storage_provider=self._get_storage_provider(),
            storage_path=storage_path,
            public_url=public_url,
            user_description=description,
            status=AssetStatus.PROCESSING,
            scope=resolved_scope.value,
            purpose=resolved_purpose.value,
            extraction_status=ExtractionStatus.PENDING.value,
            expires_at=expires_at,
        )

        created_asset = self.repository.create(asset)

        # 5. Trigger AI image pipeline (legacy) — only for image assets.
        if background_tasks and asset_type == AssetType.IMAGE:
            background_tasks.add_task(
                self._process_asset_task,
                created_asset.id,
                tenant_id,
                storage_path,
            )

        # 6. Trigger text extraction pipeline (document / audio transcript).
        # Sync by design — upload endpoints await short extraction so the very
        # next chat turn has text available. For very large docs this becomes
        # a bottleneck (future work: move to async worker with status polling).
        if asset_type in (AssetType.DOCUMENT, AssetType.AUDIO):
            try:
                AssetExtractionService(self.db).ensure_extracted(
                    created_asset.id,
                    tenant_id=tenant_id,
                )
            except Exception:
                logger.exception(
                    "asset_extraction_sync_failed",
                    asset_id=str(created_asset.id),
                )

        return created_asset

    async def _process_asset_task(
        self,
        asset_id: UUID,
        tenant_id: UUID,
        storage_path: str,
    ) -> None:
        """Background task: fetch file bytes from storage, then run AI processing."""
        try:
            from luana_core_platform.core.database import SessionLocal

            db = SessionLocal()
            repo = AssetRepository(db)

            asset = repo.get_by_id(asset_id, tenant_id=tenant_id)
            if not asset:
                return

            try:
                # Retrieve file bytes from whichever storage is active
                file_bytes = self.storage.get_file_bytes(storage_path)

                metadata = await self.processor.process_asset(asset, file_bytes)

                asset.ai_metadata = metadata
                asset.ai_description = metadata.get("ai_description")
                asset.ai_colors = metadata.get("ai_colors", [])
                asset.status = AssetStatus.COMPLETED

                self._update_asset_in_db(db, asset)

            except Exception as e:
                logger.exception("asset_processing_error", error=str(e))
                asset.status = AssetStatus.FAILED
                asset.error_message = str(e)
                self._update_asset_in_db(db, asset)
            finally:
                db.close()

        except Exception as e:
            logger.exception("background_task_failed", error=str(e))

    def _update_asset_in_db(self, db: Session, asset: Asset) -> None:
        from luana_core_assets.infrastructure.models.asset_model import AssetModel
        from sqlalchemy import update

        stmt = (
            update(AssetModel)
            .where(AssetModel.id == asset.id)
            .values(
                ai_metadata=asset.ai_metadata,
                ai_description=asset.ai_description,
                ai_colors=asset.ai_colors,
                status=asset.status,
                error_message=asset.error_message,
            )
        )
        db.execute(stmt)
        db.commit()

    def list_assets(
        self,
        tenant_id: UUID,
        asset_type: str | None = None,
    ) -> list[Asset]:
        """List assets."""
        return self.repository.list_by_tenant(tenant_id, asset_type)

    def list_by_offer(self, offer_id: UUID) -> list[Asset]:
        """List by offer."""
        return self.repository.list_by_offer(offer_id)

    def delete_asset(
        self,
        tenant_id: UUID,
        asset_id: UUID,
        offer_id: UUID | None = None,
    ) -> bool:
        """Delete asset."""
        asset = self.repository.get_by_id(asset_id, tenant_id=tenant_id)
        if not asset or str(asset.tenant_id) != str(tenant_id):
            return False

        if offer_id and asset.offer_id and str(asset.offer_id) != str(offer_id):
            return False

        if asset.storage_path:
            self.storage.delete(asset.storage_path)

        return self.repository.delete(asset_id)
