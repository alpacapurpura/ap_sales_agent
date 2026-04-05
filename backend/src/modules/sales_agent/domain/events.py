import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    occurred_on: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1

    class Config:
        arbitrary_types_allowed = True
