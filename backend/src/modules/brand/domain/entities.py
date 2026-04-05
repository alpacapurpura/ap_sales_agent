from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from src.shared.domain.base_entity import BaseEntity


class ExtractRequest(BaseEntity):
    url: str = Field(..., description="URL to scrape")
    type: Literal["brand_identity"] = Field(
        "brand_identity", description="Type of extraction to perform"
    )


class Avatar(BaseEntity):
    id: UUID
    tenant_id: UUID | None = None
    user_id: UUID | None = None
    name: str
    scope: str = "GLOBAL"
    icp_description: str | None = None
    anti_avatar: str | None = None
    voice_tone_config: dict[str, Any] = {}
    is_default: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
