"""Assets CRUD endpoints for the offer header Assets tab.

Delegates to ``OfferAssetService`` with an in-process file-storage stub.
The real R2/S3 backend will be wired later without touching this router.
"""

from datetime import timedelta
from io import BytesIO
from typing import BinaryIO
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.api.dto.asset_dtos import (
    AssetDownloadUrlResponse,
    AssetGenerateRequest,
    AssetListResponse,
    AssetUpdateRequest,
    OfferAssetResponse,
)
from src.modules.offer.application.ports import IFileStoragePort
from src.modules.offer.application.services.offer_asset_service import (
    OfferAssetService,
)
from src.modules.offer.domain.enums import AssetSource, AssetType
from src.modules.offer.domain.exceptions import AssetNotFoundError
from src.modules.offer.infrastructure.repositories.offer_asset_repository import (
    OfferAssetRepository,
)
from src.shared.domain.datetime_utils import utc_now

router = APIRouter()


class _StubFileStorage(IFileStoragePort):
    """In-process file-storage stub.

    Fakes R2/S3 semantics: ``upload`` returns a synthetic URL and the byte
    count, ``get_signed_url`` echoes the URL, and ``delete`` is a no-op.
    The real adapter will be injected via FastAPI ``Depends`` once the
    storage backend lands.
    """

    def upload(
        self,
        tenant_id: UUID,
        folder: str,
        filename: str,
        content: BinaryIO,
        mime_type: str,
    ) -> tuple[str, int]:
        data = content.read() if hasattr(content, "read") else b""
        size = len(data) if isinstance(data, (bytes, bytearray)) else 0
        url = f"https://stub.local/{tenant_id}/{folder}/{uuid4().hex}-{filename}"
        return url, size

    def get_download_stream(self, file_url: str) -> BinaryIO:
        return BytesIO(b"")

    def get_signed_url(self, file_url: str, *, expires_in: int = 900) -> str:
        return file_url

    def delete(self, file_url: str) -> None:
        return None


def _service(db: Session) -> OfferAssetService:
    return OfferAssetService(
        asset_repo=OfferAssetRepository(db),
        file_storage=_StubFileStorage(),
    )


def _to_response(asset) -> OfferAssetResponse:  # type: ignore[no-untyped-def]
    return OfferAssetResponse.model_validate(
        {
            "id": asset.id,
            "offer_id": asset.offer_id,
            "name": asset.name,
            "type": asset.type,
            "source": asset.source,
            "status": asset.status,
            "file_url": asset.file_url,
            "thumbnail_url": asset.thumbnail_url,
            "mime_type": asset.mime_type,
            "size_bytes": asset.size_bytes,
            "metadata": asset.metadata,
            "editable_in_puck": asset.editable_in_puck,
            "error_message": asset.error_message,
            "created_at": asset.created_at,
            "updated_at": asset.updated_at,
        }
    )


@router.get("/{offer_id}/assets", response_model=AssetListResponse)
async def list_assets(
    offer_id: str,
    search: str | None = Query(None),
    type: AssetType | None = Query(None),
    source: AssetSource | None = Query(None),
    sort: str = Query("created_desc"),
    limit: int = Query(24, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AssetListResponse:
    items, total = _service(db).list_assets(
        tenant_id=user.tenant_id,
        offer_id=UUID(offer_id),
        search=search,
        type=type,
        source=source,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return AssetListResponse(
        items=[_to_response(a) for a in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{offer_id}/assets/upload",
    response_model=OfferAssetResponse,
    status_code=201,
)
async def upload_asset(
    offer_id: str,
    file: UploadFile = File(...),
    name: str = Form(...),
    type: AssetType = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OfferAssetResponse:
    content = await file.read()
    asset = _service(db).upload_asset(
        tenant_id=user.tenant_id,
        offer_id=UUID(offer_id),
        file_bytes=content,
        filename=file.filename or name,
        type=type,
    )
    return _to_response(asset)


@router.post(
    "/{offer_id}/assets/generate",
    response_model=OfferAssetResponse,
    status_code=201,
)
async def generate_asset(
    offer_id: str,
    body: AssetGenerateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OfferAssetResponse:
    asset = _service(db).generate_asset(
        tenant_id=user.tenant_id,
        offer_id=UUID(offer_id),
        type=body.type,
        prompt_params=body.prompt_params,
        name=body.name,
    )
    return _to_response(asset)


@router.get("/{offer_id}/assets/{asset_id}", response_model=OfferAssetResponse)
async def get_asset(
    offer_id: str,
    asset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OfferAssetResponse:
    try:
        asset = _service(db).get_asset(
            tenant_id=user.tenant_id,
            offer_id=UUID(offer_id),
            asset_id=UUID(asset_id),
        )
    except AssetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_response(asset)


@router.patch("/{offer_id}/assets/{asset_id}", response_model=OfferAssetResponse)
async def update_asset(
    offer_id: str,
    asset_id: str,
    body: AssetUpdateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OfferAssetResponse:
    try:
        asset = _service(db).update_asset(
            tenant_id=user.tenant_id,
            offer_id=UUID(offer_id),
            asset_id=UUID(asset_id),
            fields=body.model_dump(exclude_unset=True),
        )
    except AssetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_response(asset)


@router.delete("/{offer_id}/assets/{asset_id}", status_code=204)
async def delete_asset(
    offer_id: str,
    asset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    try:
        _service(db).delete_asset(
            tenant_id=user.tenant_id,
            offer_id=UUID(offer_id),
            asset_id=UUID(asset_id),
        )
    except AssetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/{offer_id}/assets/{asset_id}/download",
    response_model=AssetDownloadUrlResponse,
)
async def get_asset_download_url(
    offer_id: str,
    asset_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AssetDownloadUrlResponse:
    try:
        url = _service(db).get_download_url(
            tenant_id=user.tenant_id,
            offer_id=UUID(offer_id),
            asset_id=UUID(asset_id),
        )
    except AssetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AssetDownloadUrlResponse(
        url=url,
        expires_at=utc_now() + timedelta(minutes=15),
    )
