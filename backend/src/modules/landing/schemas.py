"""Pydantic schemas for the landing module."""

from typing import Any

from pydantic import BaseModel


class RegenerateBlockRequest(BaseModel):
    """Schema for regenerate block request."""

    current_content: str
    block_type: str
    context: dict[str, Any] | None = None


class RegenerateBlockResponse(BaseModel):
    """Regenerated block content returned by the AI."""

    content: str
