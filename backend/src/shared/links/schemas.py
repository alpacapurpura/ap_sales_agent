"""Pydantic schemas for shareable link API responses."""

from typing import Any

from pydantic import BaseModel


class LinkResolveResponse(BaseModel):
    """Response DTO for resolving a shareable link token."""

    valid: bool
    type: str
    tenant_name: str
    tenant_avatar: str | None = None
    params: dict[str, Any] = {}
