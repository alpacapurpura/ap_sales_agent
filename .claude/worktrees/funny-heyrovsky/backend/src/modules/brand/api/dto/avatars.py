from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
import uuid

class AvatarBase(BaseModel):
    name: str
    icp_description: Optional[str] = ""
    anti_avatar: Optional[str] = ""
    voice_tone_config: Optional[Dict[str, Any]] = {}
    scope: Optional[str] = "GLOBAL"

class AvatarCreate(AvatarBase):
    pass

class AvatarUpdate(BaseModel):
    name: Optional[str] = None
    icp_description: Optional[str] = None
    anti_avatar: Optional[str] = None
    voice_tone_config: Optional[Dict[str, Any]] = None
    scope: Optional[str] = None

class AvatarResponse(AvatarBase):
    id: uuid.UUID
    is_default: bool
    created_at: Any # datetime

    model_config = ConfigDict(from_attributes=True)
