"""HookRegistry — protocol for the copilot event-subscription bus.

See CONTRACT §16.2.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol, runtime_checkable

HookHandler = Callable[[object], Awaitable[None]]


@runtime_checkable
class HookRegistry(Protocol):
    """Port for the event bus used by the copilot."""

    def subscribe(
        self,
        event_type: type,
        handler: HookHandler,
        *,
        name: str,
    ) -> None:
        """Register ``handler`` for ``event_type`` under a stable ``name``."""
        ...

    def unsubscribe(self, name: str) -> None:
        """Remove a previously registered handler by ``name``. No-op if absent."""
        ...

    def handlers_for(self, event_type: type) -> list[HookHandler]:
        """Return handlers registered for ``event_type`` (empty list if none)."""
        ...

    async def emit(self, event: object) -> None:
        """Dispatch ``event`` to all matching handlers. Fire-and-forget; must never block."""
        ...
