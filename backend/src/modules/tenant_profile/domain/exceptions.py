"""Domain exceptions for the tenant_profile bounded context.

All exceptions are pure Python — no HTTP status codes. The API layer translates
domain exceptions into appropriate HTTP responses.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


class DomainError(Exception):
    """Base class for all tenant_profile domain errors."""


class BusinessTypesChangeRateLimitedError(DomainError):
    """Raised when an update is attempted within the 30-day rate-limit window.

    Attributes:
        next_allowed_at: The first UTC timestamp at which a new change is
            permitted. Surfaced in the 409 response body so the UI can render
            ``"Próxima edición disponible: {date}"``.
    """

    def __init__(self, next_allowed_at: datetime) -> None:
        """Capture the soonest UTC timestamp when a change is permitted."""
        self.next_allowed_at = next_allowed_at
        super().__init__(f"business_types change rate-limited until {next_allowed_at.isoformat()}")
