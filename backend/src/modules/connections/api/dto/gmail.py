from pydantic import BaseModel


class GmailStatusResponse(BaseModel):
    is_connected: bool
    email: str | None = None
