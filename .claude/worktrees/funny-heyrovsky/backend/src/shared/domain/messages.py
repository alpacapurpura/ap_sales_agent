from typing import Dict, Any, Optional
from src.shared.domain.base_entity import BaseEntity

class IncomingMessage(BaseEntity):
    user_id: str
    text: str
    channel_type: str
    metadata: Dict[str, Any] = {}

class OutgoingMessage(BaseEntity):
    user_id: str
    text: str
    channel_type: Optional[str] = None
    metadata: Dict[str, Any] = {}
