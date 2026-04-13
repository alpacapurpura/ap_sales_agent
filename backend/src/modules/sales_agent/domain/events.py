"""Events domain module."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from src.shared.domain.datetime_utils import utc_now


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    occurred_on: datetime = Field(default_factory=utc_now)
    version: int = 1

    class Config:
        """Model configuration."""

        arbitrary_types_allowed = True
