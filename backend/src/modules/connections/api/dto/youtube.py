from pydantic import BaseModel
from typing import Optional, Dict, Any

class YoutubeStatusResponse(BaseModel):
    is_connected: bool
    is_configured: bool
    channel_id: Optional[str] = None
    channel_title: Optional[str] = None
    channel_data: Optional[Dict[str, Any]] = None
