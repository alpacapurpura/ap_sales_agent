"""Paginated response wrapper used by all list endpoints."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound=BaseModel)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response wrapper.

    Used by all list endpoints. limit/offset enforced at API layer.
    has_more = True signals client to fetch next page.
    """

    model_config = ConfigDict(extra="forbid")

    items: list[T]
    total_count: int = Field(..., ge=0)
    limit: int = Field(..., ge=1, le=100)
    offset: int = Field(..., ge=0)
    has_more: bool
