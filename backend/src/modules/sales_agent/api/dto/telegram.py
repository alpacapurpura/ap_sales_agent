from pydantic import BaseModel
from typing import Optional, Dict, Any

class TelegramConnectRequest(BaseModel):
    token: str

class ChannelStatusResponse(BaseModel):
    is_connected: bool
    bot_name: Optional[str] = None
    username: Optional[str] = None
    config: Dict[str, Any] = {}

class TelegramConfigRequest(BaseModel):
    config: Dict[str, Any]
