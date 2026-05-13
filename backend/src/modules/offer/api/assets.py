"""Assets CRUD endpoints for the offer header Assets tab.

Delegates to ``OfferAssetService`` with an in-process file-storage stub.
The real R2/S3 backend will be wired later without touching this router.
"""

from datetime import timedelta
from io import BytesIO
from typing import Annotated, BinaryIO
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
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_offer_studio.api.dto.asset_dtos import (
    AssetDownloadUrlResponse,
    AssetGenerateRequest,
    AssetListResponse,
    AssetUpdateRequest,
    OfferAssetResponse,
)
from luana_core_offer_studio.application.ports import IFileStoragePort
from luana_core_offer_studio.application.services.offer_asset_service import (
    OfferAssetService,
)
from luana_core_offer_studio.domain.enums import AssetSource, AssetType
from luana_core_offer_studio.domain.exceptions import AssetNotFoundError
from luana_core_offer_studio.infrastructure.models.offer_asset_model import OfferAssetModel
from luana_core_offer_studio.infrastructure.repositories.offer_asset_repository import (
    OfferAssetRepository,
)
from luana_core_platform.core.database import get_db
from luana_core_platform.domain.datetime_utils import utc_now
from sqlalchemy.orm import Session

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


def _to_response(asset: OfferAssetModel) -> OfferAssetResponse:
    # Accept either the SA model (legacy) or the domain entity — the
    # ``list_assets`` path now returns domain objects, the single-asset
    # paths still walk through model-shaped dicts.
    metadata = getattr(asset, "metadata_json", None)
    if metadata is None:
        metadata = getattr(asset, "metadata", None) or {}

    return OfferAssetResponse.model_validate(
        {
            "id": asset.id,
            "offer_id": asset.offer_id,
            "edition_id": getattr(asset, "edition_id", None),
            "shared_across_editions": bool(getattr(asset, "shared_across_editions", False)),
            "name": asset.name,
            "type": asset.type,
            "source": asset.source,
            "status": asset.status,
            "file_url": asset.file_url,
            "thumbnail_url": asset.thumbnail_url,
            "mime_type": asset.mime_type,
            "size_bytes": asset.size_bytes,
            "metadata": metadata,
            "editable_in_puck": asset.editable_in_puck,
            "error_message": asset.error_message,
            "created_at": asset.created_at,
            "updated_at": asset.updated_at,
        },
    )


@router.get("/{offer_id}/assets")
async def list_assets(
    offer_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    search: Annotated[str | None, Query()] = None,
    type_: Annotated[AssetType | None, Query(alias="type")] = None,
    source: Annotated[AssetSource | None, Query()] = None,
    edition_id: Annotated[UUID | None, Query()] = None,
    sort: Annotated[str, Query()] = "created_desc",
    limit: Annotated[int, Query(ge=1, le=200)] = 24,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AssetListResponse:
    """List assets.

    ``edition_id`` filter:

    - omitted → offer-wide listing (legacy, unchanged).
    - set → edition-scoped (assets bound to this edition + shared assets).
    """
    items, total = _service(db).list_assets(
        tenant_id=user.tenant_id,
        offer_id=UUID(offer_id),
        search=search,
        type_=type_,
        source=source,
        edition_id=edition_id,
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
    status_code=201,
)
async def upload_asset(
    offer_id: str,
    file: Annotated[UploadFile, File()],
    name: Annotated[str, Form()],
    type_: Annotated[AssetType, Form(alias="type")],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    edition_id: Annotated[UUID | None, Form()] = None,
    shared_across_editions: Annotated[bool, Form()] = False,
) -> OfferAssetResponse:
    """Upload asset, optionally bound to a launch edition."""
    content = await file.read()
    asset = _service(db).upload_asset(
        tenant_id=user.tenant_id,
        offer_id=UUID(offer_id),
        file_bytes=content,
        filename=file.filename or name,
        type_=type_,
        edition_id=edition_id,
        shared_across_editions=shared_across_editions,
    )
    return _to_response(asset)


@router.post(
    "/{offer_id}/assets/generate",
    status_code=201,
)
async def generate_asset(
    offer_id: str,
    body: AssetGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> OfferAssetResponse:
    """Generate asset, optionally bound to a launch edition."""
    asset = _service(db).generate_asset(
        tenant_id=user.tenant_id,
        offer_id=UUID(offer_id),
        type_=body.type,
        prompt_params=body.prompt_params,
        name=body.name,
        edition_id=body.edition_id,
        shared_across_editions=body.shared_across_editions,
    )
    return _to_response(asset)


@router.get("/{offer_id}/assets/{asset_id}")
async def get_asset(
    offer_id: str,
    asset_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> OfferAssetResponse:
    """Retrieve asset."""
    try:
        asset = _service(db).get_asset(
            tenant_id=user.tenant_id,
            offer_id=UUID(offer_id),
            asset_id=UUID(asset_id),
        )
    except AssetNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_response(asset)


@router.patch("/{offer_id}/assets/{asset_id}")
async def update_asset(
    offer_id: str,
    asset_id: str,
    body: AssetUpdateRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> OfferAssetResponse:
    """Update asset."""
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
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Delete asset."""
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
)
async def get_asset_download_url(
    offer_id: str,
    asset_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> AssetDownloadUrlResponse:
    """Retrieve asset download url."""
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
