"""F11.1 — `CopilotOrchestrator._record_routing_decision` writes to copilot_routing_log.

Heredado F8/F9: ``build_default_router`` factory + admin page existían pero el
chat orchestrator nunca llamaba ``router.select(...)``. F11 wirea la
telemetría: cada turn debe insertar un row en ``copilot_routing_log`` para
que el admin Streamlit ``/copilot-routing`` muestre datos reales.

Estos tests cubren el helper aislado (insertion + resilience). El call site
(`stream_chat`) está cubierto por la suite full + smoke; mockear todo el
graph sería frágil y no aporta cobertura adicional sobre la lógica de F11.1.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from luana_core_copilot.application.orchestrator.chat import CopilotOrchestrator
from luana_core_copilot.domain.events import EVENT_ROUTING_DECIDED
from luana_core_platform.core.enums import ModelRole
from luana_core_copilot.domain.routing_policy import (
    ClassifierType,
    RoutingDecision,
)
from luana_core_copilot.infrastructure.models.routing_log_model import RoutingLogModel
from luana_core_copilot.infrastructure.repositories.routing_log_repository import (
    RoutingLogRepository,
)
from luana_core_platform.domain.events import EventBus

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@pytest.fixture
def orchestrator(db: Session) -> CopilotOrchestrator:
    return CopilotOrchestrator(db)


@pytest.fixture
def routing_events() -> list:
    """Capture every ``copilot_routing_decided`` event published during the test."""
    captured: list = []
    EventBus.clear()

    def _capture(ev) -> None:
        captured.append(ev)

    EventBus.subscribe(EVENT_ROUTING_DECIDED, _capture)
    yield captured
    EventBus.clear()


def _state(*, current_route: str | None = None, guided_mode: bool = False) -> dict:
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


class _StubRouter:
    """Returns a deterministic decision; never touches LLM."""

    def __init__(self, decision: RoutingDecision) -> None:
        self._decision = decision
        self.calls: list = []

    def select(self, request: object) -> RoutingDecision:
        self.calls.append(request)
        return self._decision


class TestRecordRoutingDecision:
    def test_persists_routing_log_row(
        self,
        orchestrator: CopilotOrchestrator,
        db: Session,
        routing_events: list,
    ) -> None:
        tenant_id = uuid4()
        conv_id = uuid4()
        msg_id = uuid4()
        decision = RoutingDecision(
            role=ModelRole.FAST,
            reason="rule:short_msg",
            confidence=0.92,
            classifier_used=ClassifierType.RULE,
            fallback_role=ModelRole.FAST,
        )
        router = _StubRouter(decision)

        orchestrator._record_routing_decision(
            tenant_id=tenant_id,
            conversation_id=conv_id,
            message_id=msg_id,
            user_msg="hola",
            state=_state(current_route="/dashboard"),
            router=router,
        )

        rows = RoutingLogRepository(db).list_by_conversation(
            tenant_id=tenant_id,
            conversation_id=conv_id,
        )
        assert len(rows) == 1
        row = rows[0]
        assert row.message_id == msg_id
        assert row.role_selected == "fast"
        assert row.classifier_used == "rule"
        assert row.reason == "rule:short_msg"
        assert float(row.confidence) == pytest.approx(0.92)
        assert row.user_msg_length == len("hola")

        # The orchestrator publishes a RoutingDecided event with the same
        # shape so the observability subscriber can mirror it into
        # copilot_trace_event.
        assert len(routing_events) == 1
        ev = routing_events[0]
        assert ev.payload["role"] == "fast"
        assert ev.payload["classifier"] == "rule"
        assert ev.payload["confidence"] == "0.92"

    def test_router_request_uses_current_route_and_mode(
        self,
        orchestrator: CopilotOrchestrator,
        db: Session,
    ) -> None:
        decision = RoutingDecision(
            role=ModelRole.NANO,
            reason="default_short",
            confidence=None,
            classifier_used=ClassifierType.DEFAULT,
            fallback_role=ModelRole.FAST,
        )
        router = _StubRouter(decision)

        orchestrator._record_routing_decision(
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            message_id=uuid4(),
            user_msg="que tal",
            state=_state(current_route="/brand-studio", guided_mode=True),
            router=router,
        )

        assert len(router.calls) == 1
        req = router.calls[0]
        assert req.user_msg == "que tal"
        assert req.route == "/brand-studio"
        assert req.mode == "procedure"
        assert req.procedure_active is True

    def test_router_failure_does_not_raise(
        self,
        orchestrator: CopilotOrchestrator,
        db: Session,
    ) -> None:
        class ExplodingRouter:
            def select(self, _request: object) -> RoutingDecision:
                msg = "router down"
                raise RuntimeError(msg)

        # Should swallow + log, NOT raise.
        orchestrator._record_routing_decision(
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            message_id=uuid4(),
            user_msg="hola",
            state=_state(),
            router=ExplodingRouter(),
        )
        # No row persisted.
        assert db.query(RoutingLogModel).count() == 0

    def test_default_classifier_persists_null_confidence(
        self,
        orchestrator: CopilotOrchestrator,
        db: Session,
    ) -> None:
        tenant_id = uuid4()
        decision = RoutingDecision(
            role=ModelRole.FAST,
            reason="no_rule_matched",
            confidence=None,
            classifier_used=ClassifierType.DEFAULT,
            fallback_role=ModelRole.FAST,
        )
        router = _StubRouter(decision)

        orchestrator._record_routing_decision(
            tenant_id=tenant_id,
            conversation_id=uuid4(),
            message_id=uuid4(),
            user_msg="x" * 200,
            state=_state(),
            router=router,
        )

        rows = RoutingLogRepository(db).list_by_tenant(tenant_id=tenant_id)
        assert len(rows) == 1
        assert rows[0].confidence is None
        assert rows[0].classifier_used == "default"
