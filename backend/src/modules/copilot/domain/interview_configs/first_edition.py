"""Schema for the Copilot interview's ``first_edition_date`` block (Phase 7).

Captured at the final block of the offer interview for edition-supporting
archetypes. If ``start_date`` is provided, the follow-up procedure
publishes the placeholder edition (DRAFT + PRIVATE → UPCOMING + PUBLIC).
If ``start_date`` is None, the placeholder stays DRAFT + PRIVATE and
leads captured meanwhile are added to the offer's waitlist.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FirstEditionInput(BaseModel):
    """Captured answer for the ``first_edition_date`` interview block."""

    model_config = ConfigDict(populate_by_name=True)

    start_date: datetime | None = Field(
        default=None,
        description="ISO 8601 timestamp for when the first edition kicks off. Null means user skipped.",
    )
    end_date: datetime | None = Field(
        default=None,
        description="Optional end timestamp — not required to publish.",
    )
    location_override: dict[str, Any] | None = Field(
        default=None,
        description="Per-edition override for format/platform (e.g. {'format': 'virtual', 'platform': 'Zoom'}).",
    )


__all__ = ["FirstEditionInput"]
