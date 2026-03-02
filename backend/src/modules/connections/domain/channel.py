from typing import Dict, Any, Optional
from pydantic import Field
from uuid import UUID
from datetime import datetime
from src.shared.domain.base_entity import BaseEntity
from src.modules.connections.domain.enums import ChannelType

class ChannelConnection(BaseEntity):
    id: UUID
    tenant_id: UUID
    channel_type: ChannelType
    
    # Credentials (e.g., {"bot_token": "..."})
    credentials: Dict[str, Any] = Field(default_factory=dict)
    
    # Configuration (e.g., {"welcome_message": "...", "bot_name": "..."})
    config: Dict[str, Any] = Field(default_factory=dict)
    
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
