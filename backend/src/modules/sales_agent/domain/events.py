from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from typing import Optional

class DomainEvent(BaseModel):
    """Base class for all domain events."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    occurred_on: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    
    class Config:
        arbitrary_types_allowed = True
