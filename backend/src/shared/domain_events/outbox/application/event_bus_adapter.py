"""EventBusAdapter — backwards-compatible shim for 38 EventBus.publish call sites.

Single public API: ``publish(event, session=None, *, module=None, idempotency_key=None)``.
Signature is identical to the legacy ``EventBus.publish``.

Behavior matrix (Q4 PM resolution):
| flag ON | session      | path                                              |
|---------|--------------|---------------------------------------------------|
| no      | any          | LegacyEventBus.publish (zero change)              |
| yes     | sync Session | enqueue via sync bridge (INSERT via sync session) |
| yes     | AsyncSession | enqueue via async path (await)                    |
| yes     | None         | log warning + LegacyEventBus.publish (no DB ctx)  |

Module inference (F-1 fix, PI-1 S0 post-REVIEW):
When ``module=None`` (the 38 production call sites never pass it), the adapter
walks the Python call-stack up to ``_FRAME_DEPTH_LIMIT`` frames looking for a
frame whose ``__file__`` matches ``src/modules/{name}/``.  The first match
wins and is cached per (tenant_id, event_class) by the caller — here we cache
per calling-frame filename to keep inference O(1) on repeat calls from the same
file.

Cache: ``functools.lru_cache`` on the per-filename helper (unbounded — the set
of emitter files is finite and stable; clear in tests via
``_reset_module_inference_cache()``).

See CONTRACT.md §1.A.5 for full decision rationale.
"""

from __future__ import annotations

import re
import sys
from functools import cache
from typing import TYPE_CHECKING, Any

import structlog

from src.core.config import settings

if TYPE_CHECKING:
    from src.shared.domain_events.outbox.domain.event import DomainEvent

logger = structlog.get_logger(__name__)

# Maximum number of frames to walk when inferring the calling module.
# 15 is sufficient to cover deeply nested tool → service → repo call chains
# without unbounded stack walks.
_FRAME_DEPTH_LIMIT: int = 15

# Matches ``…/src/modules/<name>/…`` in a file path.
_MODULE_PATH_RE: re.Pattern[str] = re.compile(r"[/\\]src[/\\]modules[/\\]([a-zA-Z_][a-zA-Z0-9_]*)[/\\]")


@cache
def _module_name_from_file(filename: str) -> str | None:
    """Return the Nicolify module name extracted from *filename*, or ``None``.

    Cached per filename — the emitter file set is stable at runtime.
    Result is ``None`` for frames outside ``src/modules/``.
    """
    m = _MODULE_PATH_RE.search(filename)
    return m.group(1) if m else None


def _infer_module_from_caller() -> str | None:
    """Walk the call stack to find the first frame inside ``src/modules/``.

    Returns the module name (e.g. ``"sales_agent"`` or ``"copilot"``) or
    ``None`` if no matching frame found within ``_FRAME_DEPTH_LIMIT``.

    Uses ``sys._getframe()`` for performance — ``inspect.stack()`` builds
    a full FrameInfo list which is expensive for hot-path publish calls.
    """
    try:
        frame = sys._getframe(0)
        depth = 0
        while frame is not None and depth < _FRAME_DEPTH_LIMIT:
            filename = frame.f_code.co_filename
            module_name = _module_name_from_file(filename)
            if module_name is not None:
                return module_name
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1
    except (AttributeError, ValueError):
        # Raised by sys._getframe in some edge cases (C extensions, etc.)
        pass
    return None


def _reset_module_inference_cache() -> None:
    """Clear the lru_cache — used in test isolation.

    Tests that change the import structure or monkeypatch file paths need
    to call this between test cases to avoid stale cache entries.
    """
    _module_name_from_file.cache_clear()


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

        ``module`` inference (F-1 fix):
        When ``module=None`` (the 38 production call-sites), the adapter infers
        the module by walking the call stack.  Explicit ``module=`` kwarg still
        takes precedence so tests can override.
        """
        from src.shared.domain.events import EventBus as LegacyEventBus

        # F-1: Infer module when not explicitly provided.
        resolved_module = module if module is not None else _infer_module_from_caller()

        if not self._is_outbox_enabled(resolved_module):
            LegacyEventBus.publish(event, session=session)
            return

        # Flag ON path
        if session is None:
            logger.warning(
                "outbox_skip_no_session",
                event_name=event.event_name,
                module=resolved_module,
            )
            LegacyEventBus.publish(event, session=None)
            return

        # F-2: Explicit async/sync dispatch — no event-loop trickery.
        # _is_async_session uses isinstance check; no try/except needed here.
        if _is_async_session(session):
            import asyncio

            outbox = self._get_outbox()
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule coroutine on the running loop.
                    # fire-and-forget intentional: outbox failure MUST NOT
                    # break the caller's turn (best-effort contract).
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
                    module=resolved_module,
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
                module=resolved_module,
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
        """Check feature flag for the given module.

        ``module=None`` means inference failed → falls back to
        ``USE_OUTBOX_PATTERN_DEFAULT`` (False by default, preserving
        legacy behavior for any call-site we could not classify).
        """
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
