"""EventBusAdapter — backwards-compatible shim for 38 EventBus.publish call sites.

Single public API: ``publish(event, session=None, *, module=None, idempotency_key=None)``.
Signature is identical to the legacy ``EventBus.publish``.

Behavior matrix (Q4 PM resolution):
| flag ON | session      | path                                              |
|---------|--------------|---------------------------------------------------|
| no      | any          | LegacyEventBus.publish (zero change)              |
| yes     | sync Session | enqueue via sync bridge (INSERT via sync session) |
| yes     | AsyncSession | enqueue via async path                            |
| yes     | None         | log warning + LegacyEventBus.publish (no DB ctx)  |

See CONTRACT.md §1.A.5 for full decision rationale.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from src.core.config import settings

if TYPE_CHECKING:
    from src.shared.domain_events.outbox.domain.event import DomainEvent

logger = structlog.get_logger(__name__)


class EventBusAdapter:
    """Compat shim. Exported as ``EventBus`` from ``shared/domain/events.py`` shim.

    Instantiated once at startup. Uses lazy import of OutboxService to avoid
    circular imports during module load.
    """

    def __init__(self, outbox_service: Any | None = None) -> None:  # noqa: ANN401
        """Initialize adapter with optional OutboxService injection for tests."""
        # Allow injection for tests; production uses lazy default factory.
        self._outbox = outbox_service

    @staticmethod
    def subscribe(event_name: str, handler: Any) -> None:  # noqa: ANN401
        """Backwards-compat — delegates to in-memory bus.

        Subscribers in-memory continue working for call sites with flag OFF.
        """
        from src.shared.domain.events import EventBus as LegacyEventBus

        LegacyEventBus.subscribe(event_name, handler)

    @staticmethod
    def clear() -> None:
        """Clear all handlers — delegates to in-memory bus (test isolation)."""
        from src.shared.domain.events import EventBus as LegacyEventBus

        LegacyEventBus.clear()

    def publish(
        self,
        event: DomainEvent,
        session: Any | None = None,  # noqa: ANN401 — sync Session | AsyncSession | None
        *,
        module: str | None = None,
        idempotency_key: str | None = None,
    ) -> None:
        """Single API publish. Identical signature to legacy ``EventBus.publish``.

        Flag OFF (default) → legacy in-memory dispatch (zero behavioral change).
        Flag ON → outbox INSERT inside caller's transaction.
        """
        from src.shared.domain.events import EventBus as LegacyEventBus

        if not self._is_outbox_enabled(module):
            LegacyEventBus.publish(event, session=session)
            return

        # Flag ON path
        if session is None:
            logger.warning(
                "outbox_skip_no_session",
                event_name=event.event_name,
                module=module,
            )
            LegacyEventBus.publish(event, session=None)
            return

        if _is_async_session(session):
            # Async path — schedule outbox INSERT
            outbox = self._get_outbox()
            import asyncio

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    _task = loop.create_task(  # noqa: RUF006 — fire-and-forget intentional
                        outbox.enqueue_async_from_sync_caller(
                            event,
                            session=session,
                            idempotency_key=idempotency_key,
                        )
                    )
                else:
                    loop.run_until_complete(
                        outbox.enqueue_async_from_sync_caller(
                            event,
                            session=session,
                            idempotency_key=idempotency_key,
                        )
                    )
            except Exception:  # noqa: BLE001 — best-effort, must not break caller
                logger.warning(
                    "outbox_async_enqueue_failed",
                    event_name=event.event_name,
                    module=module,
                    exc_info=True,
                )
            return

        # Sync path — Session (psycopg2). 75%+ of the 38 sites.
        outbox = self._get_outbox()
        try:
            outbox.enqueue_sync(
                event,
                session=session,
                idempotency_key=idempotency_key,
            )
        except Exception:  # noqa: BLE001 — best-effort, must not break caller
            logger.warning(
                "outbox_sync_enqueue_failed",
                event_name=event.event_name,
                module=module,
                exc_info=True,
            )

    def _get_outbox(self) -> Any:  # noqa: ANN401
        """Lazy factory — avoids circular imports at module load time."""
        if self._outbox is None:
            from src.shared.domain_events.outbox.application.outbox_service import OutboxService

            self._outbox = OutboxService()
        return self._outbox

    @staticmethod
    def _is_outbox_enabled(module: str | None) -> bool:
        """Check feature flag for the given module."""
        if module is None:
            return settings.USE_OUTBOX_PATTERN_DEFAULT
        flag_attr = f"USE_OUTBOX_PATTERN_{module.upper()}"
        return getattr(settings, flag_attr, settings.USE_OUTBOX_PATTERN_DEFAULT)


def _is_async_session(session: Any) -> bool:  # noqa: ANN401
    """Return True if session is an AsyncSession instance."""
    try:
        from sqlalchemy.ext.asyncio import AsyncSession

        return isinstance(session, AsyncSession)
    except ImportError:
        return False


# Module-level singleton used by the legacy shim and by emitter imports.
# Exposed as public alias so callers can: ``from ... import adapter_bus as EventBus``
_adapter_instance = EventBusAdapter()
adapter_bus: EventBusAdapter = _adapter_instance
