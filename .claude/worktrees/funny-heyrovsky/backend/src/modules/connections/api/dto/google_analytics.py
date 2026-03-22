from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class GoogleAnalyticsStatusResponse(BaseModel):
    is_connected: bool
    account_summary: Optional[List[Dict[str, Any]]] = None
