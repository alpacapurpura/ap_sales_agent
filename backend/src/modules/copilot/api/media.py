"""Media upload endpoint — POST /copilot/media/upload.

# [COPILOT-MEDIA-UPLOAD] → docs/domains/copilot/CONTRACT-MULTIMODAL.md §7

Thin proxy that delegates to AssetsService.upload_asset. Zero storage duplication.
Reuses R2 strategy, AI metadata pipeline, MIME detection, and asset repository.

Auth: Clerk Bearer + X-Tenant-ID header. Rate-limited via copilot-media scope.

Allowed MIME types (per §7.4 of the contract):
- image: png, jpeg, webp, gif, svg+xml
- audio: webm, mpeg, mp4, ogg, wav
- video: mp4, webm, quicktime
- document: pdf, txt, csv, md, docx, xlsx, pptx, doc, xls
"""

from typing import Annotated, Literal
from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.assets.application.assets_service import AssetsService
from src.modules.copilot.api.media_dto import MediaUploadResponse
from src.modules.iam.api.dependencies import get_current_user

logger = structlog.get_logger()

router = APIRouter(tags=["Copilot - Media"])

# ── MIME whitelist (CONTRACT-MULTIMODAL §7.4) ─────────────────────────────────

_MIME_WHITELIST: dict[str, frozenset[str]] = {
    "image": frozenset(
        {
            "image/png",
            "image/jpeg",
            "image/webp",
            "image/gif",
            "image/svg+xml",
        }
    ),
    "audio": frozenset(
        {
            "audio/webm",
            "audio/mpeg",
            "audio/mp4",
            "audio/ogg",
            "audio/wav",
        }
    ),
    "video": frozenset(
        {
            "video/mp4",
            "video/webm",
            "video/quicktime",
        }
    ),
    "document": frozenset(
        {
            "application/pdf",
            "text/plain",
            "text/csv",
            "text/markdown",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/msword",
            "application/vnd.ms-excel",
        }
    ),
}

_MIME_TO_KIND: dict[str, str] = {}
for _kind, _mimes in _MIME_WHITELIST.items():
    for _mime in _mimes:
        _MIME_TO_KIND[_mime] = _kind

_KIND_LITERALS = Literal["image", "audio", "video", "document"]

# Default max file size: 25 MB (configurable via env in future)
_MAX_FILE_BYTES = 25 * 1024 * 1024


def _infer_kind(mime: str, declared_kind: str | None) -> str:
    """Infer the media kind from MIME type or use the declared kind."""
    if declared_kind and declared_kind in _MIME_WHITELIST:
        return declared_kind
    return _MIME_TO_KIND.get(mime, "")


def _validate_mime(mime: str, kind: str) -> None:
    """Raise 415 if the MIME type is not allowed for the given kind."""
    allowed = _MIME_WHITELIST.get(kind, frozenset())
    if mime not in allowed:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Tipo de archivo no admitido: '{mime}' para kind='{kind}'. "
                f"Tipos permitidos: {', '.join(sorted(allowed))}."
            ),
        )


@router.post(
    "/media/upload",
    summary="Subir archivo multimedia para el copilot",
)
async def upload_media(
    file: Annotated[UploadFile, File(description="Archivo a subir (imagen, audio, video o documento).")],
    background_tasks: BackgroundTasks,
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    kind: Annotated[
        str | None,
        Form(description="Tipo de archivo: image, audio, video, document. Opcional — se infiere del MIME."),
    ] = None,
    description: Annotated[
        str | None,
        Form(description="Descripción del archivo (≤240 chars). Se pasa al servicio de assets."),
    ] = None,
) -> MediaUploadResponse:
    """Subir un archivo multimedia y obtener la referencia de asset para el chat.

    El archivo se almacena en el módulo de assets (R2 o local según configuración).
    El AI metadata pipeline continúa en background.

    Returns:
        MediaUploadResponse con asset_id, public_url, mime, size_bytes, kind.

    Raises:
        400: Archivo vacío.
        413: Archivo excede el tamaño máximo (25 MB por defecto).
        415: Tipo de MIME no admitido para el kind declarado/inferido.
    """
    tenant_id: UUID = current_user.tenant_id  # type: ignore[attr-defined]

    # Read file content for size validation
    content = await file.read()
    size_bytes = len(content)

    if size_bytes == 0:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")

    if size_bytes > _MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo excede el tamaño máximo de {_MAX_FILE_BYTES // (1024 * 1024)} MB.",
        )

    mime = (file.content_type or "").strip()
    if not mime:
        raise HTTPException(status_code=415, detail="No se pudo determinar el tipo de archivo.")

    inferred_kind = _infer_kind(mime, kind)
    if not inferred_kind:
        raise HTTPException(
            status_code=415,
            detail=f"Tipo de archivo no admitido: '{mime}'.",
        )

    _validate_mime(mime, inferred_kind)

    # Truncate description to 240 chars (soft limit, per contract)
    truncated_desc = (description or "")[:240] or None

    logger.info(
        "copilot_media_upload_start",
        tenant_id=str(tenant_id),
        mime=mime,
        kind=inferred_kind,
        size_bytes=size_bytes,
        filename=file.filename,
    )

    # Seek to start for the service (content already read, pass as BytesIO)
    import io

    file_obj = io.BytesIO(content)

    # Delegate to AssetsService — single SSoT for storage (D0.2 of the contract)
    service = AssetsService(db)
    asset = service.upload_asset(
        tenant_id=tenant_id,
        file_obj=file_obj,
        filename=file.filename or f"upload.{inferred_kind}",
        mime_type=mime,
        description=truncated_desc,
        offer_id=None,  # copilot uploads are not offer-scoped
        background_tasks=background_tasks,
    )

    logger.info(
        "copilot_media_upload_done",
        tenant_id=str(tenant_id),
        asset_id=str(asset.id),
        kind=inferred_kind,
    )

    return MediaUploadResponse(
        asset_id=asset.id,
        public_url=asset.public_url,  # type: ignore[arg-type]
        mime=mime,
        size_bytes=size_bytes,
        kind=inferred_kind,  # type: ignore[arg-type]
    )
