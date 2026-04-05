from typing import Any

from pydantic import BaseModel


class LinkResolveResponse(BaseModel):
    valid: bool
    type: str
    tenant_name: str
    tenant_avatar: str | None = None
    params: dict[str, Any] = {}
