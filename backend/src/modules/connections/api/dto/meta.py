from pydantic import BaseModel
from typing import Optional, Dict, Any

class MetaStatusResponse(BaseModel):
    is_connected: bool
    name: Optional[str] = None
    account_id: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
