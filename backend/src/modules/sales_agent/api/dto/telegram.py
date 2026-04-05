from typing import Any

from pydantic import BaseModel


class TelegramConnectRequest(BaseModel):
    token: str


class ChannelStatusResponse(BaseModel):
    is_connected: bool
    bot_name: str | None = None
    username: str | None = None
    config: dict[str, Any] = {}


class TelegramConfigRequest(BaseModel):
    config: dict[str, Any]
