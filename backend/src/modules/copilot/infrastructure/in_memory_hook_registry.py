"""InMemoryHookRegistry — asyncio fire-and-forget event dispatcher.

See CONTRACT §16.2, §16.4.

Handler exceptions are swallowed + logged (``copilot.hook_failed``); they
never propagate to the emitter. Dispatch uses ``asyncio.create_task`` so a
slow handler cannot block the request path.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from src.modules.copilot.domain.hooks.hook_registry import HookHandler


_LOGGER = structlog.get_logger("copilot.hooks")


class InMemoryHookRegistry:
    """Dict-backed event bus for copilot events."""

    def __init__(self) -> None:
        """Start empty."""
        # event_type -> {name -> handler}
        self._subscribers: dict[type, dict[str, HookHandler]] = {}
        # name -> event_type (for unsubscribe)
        self._name_index: dict[str, type] = {}
        # Strong references to in-flight dispatch tasks (prevents GC).
        self._pending_tasks: set[asyncio.Task[None]] = set()

    def subscribe(
        self,
        event_type: type,
        handler: HookHandler,
        *,
        name: str,
    ) -> None:
        """Register ``handler`` for ``event_type`` under stable ``name``.

        Re-registration with the same ``name`` replaces the previous handler.
        """
        previous_event = self._name_index.get(name)
        if previous_event is not None and previous_event is not event_type:
            # Re-registering under a different event type: drop prior entry.
            self._subscribers.get(previous_event, {}).pop(name, None)
        bucket = self._subscribers.setdefault(event_type, {})
        bucket[name] = handler
        self._name_index[name] = event_type

    def unsubscribe(self, name: str) -> None:
        """Remove the handler registered under ``name``. No-op if absent."""
        event_type = self._name_index.pop(name, None)
        if event_type is None:
            return
        bucket = self._subscribers.get(event_type)
        if bucket is not None:
            bucket.pop(name, None)

    def handlers_for(self, event_type: type) -> list[HookHandler]:
        """Return handlers registered for ``event_type``."""
        bucket = self._subscribers.get(event_type)
        if not bucket:
            return []
        return list(bucket.values())

    async def emit(self, event: object) -> None:
        """Fan-out ``event`` to every matching handler; never block, never raise."""
        event_type = type(event)
        # Exact-type match (simplest dispatch — no inheritance climbing).
        handlers = list(self._subscribers.get(event_type, {}).items())

        for name, handler in handlers:
            task = asyncio.create_task(
                self._safe_dispatch(name, handler, event),
                name=f"copilot-hook:{name}",
            )
            self._pending_tasks.add(task)
            task.add_done_callback(self._pending_tasks.discard)

    @staticmethod
    async def _safe_dispatch(
        name: str,
        handler: HookHandler,
        event: object,
    ) -> None:
        """Invoke ``handler(event)`` — swallow + log any exception."""
        try:
            await handler(event)
        except Exception as exc:  # noqa: BLE001 — guard rail, never re-raise
            _LOGGER.warning(
                "copilot.hook_failed",
                handler=name,
                event_type=type(event).__name__,
                error=str(exc),
            )
