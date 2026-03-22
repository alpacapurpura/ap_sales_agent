from pydantic import BaseModel
from typing import Optional

class GmailStatusResponse(BaseModel):
    is_connected: bool
    email: Optional[str] = None
