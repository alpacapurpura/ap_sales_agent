"""Youtube DTOs."""

from typing import Any

from pydantic import BaseModel


class YoutubeStatusResponse(BaseModel):
    """Youtube Status Response DTO."""

    is_connected: bool
    is_configured: bool
    channel_id: str | None = None
    channel_title: str | None = None
    channel_data: dict[str, Any] | None = None
