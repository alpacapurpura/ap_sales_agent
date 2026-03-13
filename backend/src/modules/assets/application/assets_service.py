from typing import List, Optional, BinaryIO
import mimetypes
from uuid import UUID
import uuid
from sqlalchemy.orm import Session
from fastapi import UploadFile, BackgroundTasks
import structlog

from src.modules.assets.domain.entity import Asset
from src.modules.assets.domain.enums import AssetType, StorageProvider, AssetStatus
from src.modules.assets.infrastructure.repositories.asset_repository import AssetRepository
from src.modules.assets.infrastructure.storage import get_storage_strategy
from src.modules.assets.application.asset_processor import AssetProcessor
from src.core.config import settings

logger = structlog.get_logger()


class AssetsService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = AssetRepository(db)
        self.storage = get_storage_strategy()
        self.processor = AssetProcessor()

    def _detect_type(self, mime_type: str) -> AssetType:
        if mime_type.startswith("image/"):
            return AssetType.IMAGE
        elif mime_type.startswith("video/"):
            return AssetType.VIDEO
        elif mime_type.startswith("audio/"):
            return AssetType.AUDIO
        else:
            return AssetType.DOCUMENT

    def _get_storage_provider(self) -> StorageProvider:
        if settings.STORAGE_PROVIDER.upper() == "R2":
            return StorageProvider.R2
        return StorageProvider.LOCAL

    def upload_asset(
        self,
        tenant_id: UUID,
        file_obj: BinaryIO,
        filename: str,
        mime_type: Optional[str] = None,
        description: Optional[str] = None,
        offer_id: Optional[UUID] = None,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> Asset:

        # 1. Detect MIME Type
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
            if not mime_type:
                mime_type = "application/octet-stream"

        asset_type = self._detect_type(mime_type)

        # 2. Save File
        path_prefix = f"{str(tenant_id)}/{asset_type.lower()}"
        storage_path, public_url = self.storage.save(file_obj, filename, path_prefix)

        # 3. Create Entity
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
        )

        created_asset = self.repository.create(asset)

        # 4. Trigger AI Processing
        if background_tasks:
            background_tasks.add_task(
                self._process_asset_task,
                created_asset.id,
                storage_path,
            )

        return created_asset

    async def _process_asset_task(self, asset_id: UUID, storage_path: str):
        """Background task: fetch file bytes from storage, then run AI processing."""
        try:
            from src.core.database import SessionLocal

            db = SessionLocal()
            repo = AssetRepository(db)

            asset = repo.get_by_id(asset_id)
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
                logger.error("asset_processing_error", error=str(e))
                asset.status = AssetStatus.FAILED
                asset.error_message = str(e)
                self._update_asset_in_db(db, asset)
            finally:
                db.close()

        except Exception as e:
            logger.error("background_task_failed", error=str(e))

    def _update_asset_in_db(self, db: Session, asset: Asset):
        from src.modules.assets.infrastructure.models.asset_model import AssetModel

        db.query(AssetModel).filter(AssetModel.id == asset.id).update(
            {
                "ai_metadata": asset.ai_metadata,
                "ai_description": asset.ai_description,
                "ai_colors": asset.ai_colors,
                "status": asset.status,
                "error_message": asset.error_message,
            }
        )
        db.commit()

    def list_assets(self, tenant_id: UUID, asset_type: Optional[str] = None) -> List[Asset]:
        return self.repository.list_by_tenant(tenant_id, asset_type)

    def list_by_offer(self, offer_id: UUID) -> List[Asset]:
        return self.repository.list_by_offer(offer_id)

    def delete_asset(self, tenant_id: UUID, asset_id: UUID, offer_id: Optional[UUID] = None) -> bool:
        asset = self.repository.get_by_id(asset_id)
        if not asset or str(asset.tenant_id) != str(tenant_id):
            return False

        if offer_id and asset.offer_id and str(asset.offer_id) != str(offer_id):
            if str(asset.offer_id) != str(offer_id):
                return False

        if asset.storage_path:
            self.storage.delete(asset.storage_path)

        return self.repository.delete(asset_id)
