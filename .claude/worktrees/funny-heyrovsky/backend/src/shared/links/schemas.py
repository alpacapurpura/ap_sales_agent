from pydantic import BaseModel
from typing import Optional, Dict, Any

class LinkResolveResponse(BaseModel):
    valid: bool
    type: str
    tenant_name: str
    tenant_avatar: Optional[str] = None
    params: Dict[str, Any] = {}
