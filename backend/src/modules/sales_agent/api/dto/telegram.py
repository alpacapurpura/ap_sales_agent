"""Telegram DTOs."""

from typing import Any

from pydantic import BaseModel


class TelegramConnectRequest(BaseModel):
    """Telegram Connect Request DTO."""

    token: str


class ChannelStatusResponse(BaseModel):
    """Channel Status Response DTO."""

    is_connected: bool
    bot_name: str | None = None
    username: str | None = None
    config: dict[str, Any] = {}


class TelegramConfigRequest(BaseModel):
    """Telegram Config Request DTO."""

    config: dict[str, Any]
