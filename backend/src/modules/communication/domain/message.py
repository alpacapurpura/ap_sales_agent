from typing import Dict, Any, Optional
from pydantic import Field, ConfigDict
from uuid import UUID
from datetime import datetime
from src.shared.domain.base_entity import BaseEntity
from src.modules.communication.domain.enums import MessageSender

class Message(BaseEntity):
    id: UUID
    lead_id: Optional[UUID] = None
    tenant_id: Optional[UUID] = None
    
    sender_type: MessageSender
    content: str
    channel: Optional[str] = None # whatsapp / telegram
    external_id: Optional[str] = None # Message ID from channel
    
    metadata_info: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: Optional[datetime] = None
