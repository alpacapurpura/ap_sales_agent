"""Domain-level exceptions for the offer module.

Pure Python — no framework imports. The API layer maps these onto HTTP
status codes. Services raise these to signal business-rule violations;
callers translate at the boundary.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from luana_core_offer_studio.domain.lifecycle import OfferLifecycleStatus


class OfferDomainError(Exception):
    """Base class for all offer-module domain errors."""


class InvalidTransitionError(OfferDomainError):
    """Raised when the requested lifecycle transition is not allowed.

    Mapped to HTTP 409 Conflict at the API layer.
    """

    def __init__(
        self,
        from_status: OfferLifecycleStatus,
        to_status: OfferLifecycleStatus,
        message: str | None = None,
    ) -> None:
        """Initialize instance."""
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(
            message or (f"Invalid lifecycle transition {from_status.value} -> {to_status.value}"),
        )


class LandingNotReadyError(OfferDomainError):
    """Raised when landing generation is requested but the offer is below.

    the minimum completion threshold.

    Mapped to HTTP 409 Conflict at the API layer.
    """

    def __init__(self, offer_id: UUID, completion_percentage: float) -> None:
        """Initialize instance."""
        self.offer_id = offer_id
        self.completion_percentage = completion_percentage
        super().__init__(
            f"Offer {offer_id} is only {completion_percentage:.0f}% complete; landing generation requires >= 90%",
        )


class AssetNotFoundError(OfferDomainError):
    """Raised when an offer asset cannot be located for the tenant.

    Mapped to HTTP 404 Not Found at the API layer.
    """

    def __init__(self, asset_id: UUID) -> None:
        """Initialize instance."""
        self.asset_id = asset_id
        super().__init__(f"Offer asset {asset_id} not found")


class KnowledgeSourceNotFoundError(OfferDomainError):
    """Raised when a knowledge source cannot be located for the tenant.

    Mapped to HTTP 404 Not Found at the API layer.
    """

    def __init__(self, source_id: UUID) -> None:
        """Initialize instance."""
        self.source_id = source_id
        super().__init__(f"Knowledge source {source_id} not found")


__all__ = [
    "AssetNotFoundError",
    "InvalidTransitionError",
    "KnowledgeSourceNotFoundError",
    "LandingNotReadyError",
    "OfferDomainError",
]
