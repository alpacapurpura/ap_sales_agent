"""IntentClassifier protocol — base for all routing classifiers.

See CONTRACT §7.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from luana_core_copilot.application.router.model_router import RoutingRequest
    from luana_core_copilot.domain.routing_policy import RoutingDecision


@runtime_checkable
class IntentClassifier(Protocol):
    """A routing classifier — returns a decision or None to defer."""

    def classify(self, req: RoutingRequest) -> RoutingDecision | None:
        """Classify the request. Return ``None`` to defer to the next classifier."""
        ...
