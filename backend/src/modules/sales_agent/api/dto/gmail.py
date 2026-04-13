"""Gmail DTOs."""

from pydantic import BaseModel


class GmailStatusResponse(BaseModel):
    """Gmail Status Response DTO."""

    is_connected: bool
    email: str | None = None
