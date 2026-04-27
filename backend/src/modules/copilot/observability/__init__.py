"""Copilot observability module.

Self-contained subscription-based observability for the copilot. Wires into
LangChain via ``BaseCallbackHandler`` (standard API) and into the copilot
domain via the shared ``EventBus``. The orchestrator never imports from
here except for the single entrypoint :class:`turn_envelope.ObservabilityContext`.

Subpackages:

* ``recording``  — LangChain callback handler, domain subscribers, turn
  envelope, sanitization, low-level event store.
* ``pricing``    — Provider/model unit-cost resolver with point-in-time
  snapshots fed by a daily LiteLLM sync worker.
* ``cost``       — Cost calculator (tokens times unit price) and FX resolver
  (USD → tenant currency).
* ``persistence``— SQLAlchemy repositories for the new tables and a clean
  interface over ``copilot_trace_event``.
* ``reporting``  — Billing-cycle service and cost aggregator (Phase 3
  consumers).
* ``workers``    — ARQ background tasks (pricing sync, retention, MV
  refresh).
* ``api``        — Internal admin endpoints consumed by Streamlit (Phase
  3).

Public entrypoints (Phase 2):

* :func:`register` — call once at FastAPI app startup to wire the
  domain-event subscribers onto the shared ``EventBus``.
* :class:`ObservabilityContext` — per-turn handle imported by the
  orchestrator (re-exported from ``recording.turn_envelope``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.copilot.observability.recording.domain_subscribers import (
    register_subscribers,
)
from src.modules.copilot.observability.recording.turn_envelope import ObservabilityContext

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.modules.copilot.observability.persistence.trace_event_repository import (
        TraceEventRepository,
    )


def register(*, repo_factory: Callable[[], TraceEventRepository] | None = None) -> None:
    """Wire the observability domain-event subscribers onto the shared bus.

    Idempotent — safe to call from every FastAPI worker startup. When
    ``repo_factory`` is ``None``, defaults to a factory that opens a fresh
    sync ``Session`` and binds a ``TraceEventRepository`` to it (one short-
    lived session per dispatched event, mirroring the legacy
    ``trace_recorder._session_factory`` pattern).
    """
    factory: Callable[[], TraceEventRepository] = repo_factory or _default_repo_factory
    register_subscribers(repo_factory=factory)


def _default_repo_factory() -> TraceEventRepository:
    """Open a short-lived sync ``Session`` and return a bound repository."""
    from src.core.database import SessionLocal
    from src.modules.copilot.observability.persistence.trace_event_repository import (
        TraceEventRepository,
    )

    return TraceEventRepository(SessionLocal())


__all__ = ["ObservabilityContext", "register"]
