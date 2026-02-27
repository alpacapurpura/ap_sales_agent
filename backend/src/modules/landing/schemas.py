from pydantic import BaseModel
from typing import Optional, Dict, Any

class RegenerateBlockRequest(BaseModel):
    current_content: str
    block_type: str
    context: Optional[Dict[str, Any]] = None
