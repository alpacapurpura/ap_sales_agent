"""FP3 (B25-TP11) — Routing classifier runs in parallel with the graph stream.

Tier is telemetry-only — :func:`build_deep_agent_graph` uses
``ModelRole.AGENT`` hardcoded and ``get_tools_for_context`` resolves tools
by route, never by tier. So routing decision can run as a background task
without ANY race condition against tool binding. The classifier NANO call
(~1.7s for ambiguous >40-char messages) used to block TTFB before this
fix; now it overlaps the graph build + first model invocation.

These tests assert the parallelism contract:

- ``_record_routing_decision_async`` exists and is awaitable.
- The blocking router.select runs on a worker thread, so awaiting it
  never starves the asyncio event loop.
- A 1.0s simulated classifier delay does NOT block 50 ms of concurrent
  event-loop work.
- AC4 race-condition guard: even if the classifier returns AFTER the
  graph stream is already running, the persisted row remains coherent
  (correct tier, classifier, message_id) — no missing fields.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.modules.copilot.application.orchestrator.chat import CopilotOrchestrator
from src.modules.copilot.domain.events import EVENT_ROUTING_DECIDED
from src.core.enums import ModelRole
from src.modules.copilot.domain.routing_policy import (
    ClassifierType,
    RoutingDecision,
)
from src.modules.copilot.infrastructure.models.routing_log_model import RoutingLogModel
from src.modules.copilot.infrastructure.repositories.routing_log_repository import (
    RoutingLogRepository,
)
from src.shared.domain.events import EventBus

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@pytest.fixture
def orchestrator(db: Session) -> CopilotOrchestrator:
    return CopilotOrchestrator(db)


@pytest.fixture
def routing_events() -> list:
    captured: list = []
    EventBus.clear()

    def _capture(ev) -> None:
        captured.append(ev)

    EventBus.subscribe(EVENT_ROUTING_DECIDED, _capture)
    yield captured
    EventBus.clear()


def _state(*, current_route: str | None = "/dashboard", guided_mode: bool = False) -> dict:
    return {
        "client_context": {
            "current_route": current_route,
            "selected_fields": [],
            "form_data": {},
            "locale": "es",
            "guided_mode": guided_mode,
        },
        "active_extraction_job": None,
    }


def _decision(role: ModelRole = ModelRole.FAST) -> RoutingDecision:
    return RoutingDecision(
        role=role,
        reason="test_decision",
        confidence=0.85,
        classifier_used=ClassifierType.LLM,
        fallback_role=ModelRole.FAST,
    )


class _SlowRouter:
    """Stub router whose ``.select`` blocks ``delay_s`` on the calling thread."""

    def __init__(self, decision: RoutingDecision, delay_s: float) -> None:
        self._decision = decision
        self._delay = delay_s
        self.calls: list = []

    def select(self, request: object) -> RoutingDecision:
        self.calls.append(request)
        time.sleep(self._delay)
        return self._decision


class _ExplodingRouter:
    def select(self, _request: object) -> RoutingDecision:
        msg = "router crashed"
        raise RuntimeError(msg)


class TestRecordRoutingDecisionAsync:
    @pytest.mark.asyncio
    async def test_async_helper_exists_and_is_awaitable(
        self,
        orchestrator: CopilotOrchestrator,
    ) -> None:
        """The async variant must exist — sync version still alive for back-compat."""
        assert hasattr(orchestrator, "_record_routing_decision_async")
        assert callable(orchestrator._record_routing_decision_async)

    @pytest.mark.asyncio
    async def test_async_persists_routing_log_row(
        self,
        orchestrator: CopilotOrchestrator,
        db: Session,
        routing_events: list,
    ) -> None:
        tenant_id = uuid4()
        conv_id = uuid4()
        msg_id = uuid4()
        router = _SlowRouter(_decision(role=ModelRole.REASONING), delay_s=0.05)

        await orchestrator._record_routing_decision_async(
            tenant_id=tenant_id,
            conversation_id=conv_id,
            message_id=msg_id,
            user_msg="explica por qué los KPIs bajaron",
            state=_state(current_route="/growth-studio"),
            router=router,
        )

        rows = RoutingLogRepository(db).list_by_conversation(
            tenant_id=tenant_id,
            conversation_id=conv_id,
        )
        assert len(rows) == 1
        row = rows[0]
        assert row.message_id == msg_id
        assert row.role_selected == "reasoning"
        assert row.classifier_used == "llm"
        # The orchestrator publishes a RoutingDecided event for the
        # observability subscriber (no direct recorder call anymore).
        assert len(routing_events) == 1
        assert routing_events[0].payload["role"] == "reasoning"
        assert routing_events[0].payload["classifier"] == "llm"

    @pytest.mark.asyncio
    async def test_async_router_failure_does_not_raise(
        self,
        orchestrator: CopilotOrchestrator,
        db: Session,
    ) -> None:
        # MUST swallow + log, never raise. Telemetry resilience.
        await orchestrator._record_routing_decision_async(
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            message_id=uuid4(),
            user_msg="hola",
            state=_state(),
            router=_ExplodingRouter(),
        )
        assert db.query(RoutingLogModel).count() == 0

    @pytest.mark.asyncio
    async def test_blocking_select_runs_in_thread_does_not_starve_event_loop(
        self,
        orchestrator: CopilotOrchestrator,
    ) -> None:
        """Simulated 1.0s classifier delay + 50ms concurrent sleep should
        finish in ~1.0s total, not 1.05s. Proves the LLM call is offloaded
        to a worker thread instead of blocking ``asyncio``."""
        router = _SlowRouter(_decision(), delay_s=1.0)
        started = time.monotonic()

        routing = asyncio.create_task(
            orchestrator._record_routing_decision_async(
                tenant_id=uuid4(),
                conversation_id=uuid4(),
                message_id=uuid4(),
                user_msg="ambiguous mid-length message that won't match rule",
                state=_state(),
                router=router,
            ),
        )

        # Concurrent 50ms sleep — should run while the worker thread blocks.
        concurrent_start = time.monotonic()
        await asyncio.sleep(0.05)
        concurrent_elapsed = time.monotonic() - concurrent_start
        # Tolerance: the asyncio.sleep should resolve in ~50ms, not be
        # delayed by the routing task's blocking work.
        assert concurrent_elapsed < 0.2, f"Event loop appears blocked: 50ms sleep took {concurrent_elapsed:.3f}s"

        # The routing task should still be in flight (router.select sleeps 1.0s).
        assert not routing.done(), "Routing task finished too fast — was the LLM call offloaded?"

        await routing
        total = time.monotonic() - started
        # Total wall-clock ~1.0s — overlapping work prevented the 1.0+0.05=1.05s sequential cost.
        assert 0.95 < total < 1.5, f"Total wall-clock {total:.3f}s outside [0.95, 1.5]"

    @pytest.mark.asyncio
    async def test_ac4_no_race_condition_tier_persisted_after_stream_started(
        self,
        orchestrator: CopilotOrchestrator,
        db: Session,
    ) -> None:
        """AC4 — the classifier may resolve AFTER the graph stream has
        already produced output. The persisted row must still be coherent:
        correct tier, classifier, and message_id; no missing tools_available
        column or cross-wired fields. We simulate by spawning the routing
        task, waiting briefly (mimicking SSE block_start emission), then
        awaiting it."""
        tenant_id = uuid4()
        conv_id = uuid4()
        msg_id = uuid4()
        router = _SlowRouter(_decision(role=ModelRole.AGENT), delay_s=0.3)

        routing = asyncio.create_task(
            orchestrator._record_routing_decision_async(
                tenant_id=tenant_id,
                conversation_id=conv_id,
                message_id=msg_id,
                user_msg="audita la marca completa con plan priorizado",
                state=_state(current_route="/brand-studio"),
                router=router,
            ),
        )
        # "Stream" stand-in — yields control while the classifier resolves.
        await asyncio.sleep(0.05)
        await routing

        rows = RoutingLogRepository(db).list_by_conversation(
            tenant_id=tenant_id,
            conversation_id=conv_id,
        )
        assert len(rows) == 1
        row = rows[0]
        assert row.message_id == msg_id, "message_id wired incorrectly"
        assert row.role_selected == "agent", "tier wiring drifted"
        assert row.classifier_used == "llm"
        assert row.tools_available is not None and row.tools_available >= 0
        assert row.user_msg_length > 0
