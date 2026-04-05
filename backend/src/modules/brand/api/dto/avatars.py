import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict


class AvatarBase(BaseModel):
    name: str
    icp_description: str | None = ""
    anti_avatar: str | None = ""
    voice_tone_config: dict[str, Any] | None = {}
    scope: str | None = "GLOBAL"


class AvatarCreate(AvatarBase):
    pass


class AvatarUpdate(BaseModel):
    name: str | None = None
    icp_description: str | None = None
    anti_avatar: str | None = None
    voice_tone_config: dict[str, Any] | None = None
    scope: str | None = None


class AvatarResponse(AvatarBase):
    id: uuid.UUID
    is_default: bool
    created_at: Any  # datetime

    model_config = ConfigDict(from_attributes=True)
