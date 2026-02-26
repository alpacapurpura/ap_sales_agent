from pydantic import BaseModel, ConfigDict
from typing import Any, Dict, Optional
from datetime import datetime
import uuid

class BaseEntity(BaseModel):
    """
    Base class for all Domain Entities.
    Includes common configuration for Pydantic v2.
    """
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    def dict(self, *args, **kwargs):
        """Wrapper for model_dump to maintain compatibility if needed"""
        return self.model_dump(*args, **kwargs)
