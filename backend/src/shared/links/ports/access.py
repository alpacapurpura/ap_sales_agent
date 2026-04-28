"""AccessProvider port — S9.

Defines the Protocol for delivering digital access to a lead after payment.
Concrete adapters live in the ``connections`` module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True, slots=True)
class AccessDeliveryResult:
    """Result of a single access-delivery attempt."""

    channel: str
    success: bool
    detail: str = ""


@runtime_checkable
class AccessProvider(Protocol):
    """Strategy Protocol for access delivery channels."""

    channel: str

    def deliver_access(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        offer_id: UUID,
        metadata: dict,
    ) -> AccessDeliveryResult:
        """Deliver access to the lead. Never raises — returns a result."""
        ...
