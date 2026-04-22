"""DTOs for the copilot media upload endpoint (§7 CONTRACT-MULTIMODAL)."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, HttpUrl


class MediaUploadResponse(BaseModel):
    """Response DTO for POST /copilot/media/upload.

    # [COPILOT-MEDIA-UPLOAD] → docs/domains/copilot/CONTRACT-MULTIMODAL.md §7

    No PII fields. filename is intentionally excluded — only the UUID is canonical.
    The public_url snapshot is safe to expose (asset is tenant-scoped).
    """

    model_config = ConfigDict(from_attributes=True)

    asset_id: UUID
    public_url: HttpUrl
    mime: str
    size_bytes: int
    kind: Literal["image", "audio", "video", "document"]


__all__ = ["MediaUploadResponse"]
