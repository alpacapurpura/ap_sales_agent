"""Domain-event subscribers persist sanitised rows to sales_agent_trace_event."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest


@pytest.fixture(autouse=True)
def _stub_session_local(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Replace ``SessionLocal()`` with a mock; capture repo writes."""
    fake_session = MagicMock()
    monkeypatch.setattr(
        "src.modules.sales_agent.observability.domain_events.subscribers.SessionLocal",
        lambda: fake_session,
    )
    return fake_session


@pytest.fixture
def captured_repo_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Capture every ``SalesAgentTraceEventRepository.add(...)`` call."""
    calls: list[dict] = []

    class _CaptureRepo:
        def __init__(self, db: object) -> None:
            self.db = db

        def add(self, **kwargs: object) -> None:
            calls.append(kwargs)

    monkeypatch.setattr(
        "src.modules.sales_agent.observability.domain_events.subscribers.SalesAgentTraceEventRepository",
        _CaptureRepo,
    )
    return calls


class TestLeadQualifiedSubscriber:
    @pytest.mark.asyncio
    async def test_persists_domain_event_row(self, captured_repo_calls: list[dict]) -> None:
        from src.modules.sales_agent.domain.events import LeadQualifiedEvent
        from src.modules.sales_agent.observability.domain_events.subscribers import (
            on_lead_qualified,
        )

        tenant_id = uuid4()
        lead_id = uuid4()
        turn_id = uuid4()
        await on_lead_qualified(
            LeadQualifiedEvent(
                tenant_id=tenant_id,
                lead_id=lead_id,
                channel_type="telegram",
                turn_id=turn_id,
                lead_score=85,
                qualification_field_count=4,
                buying_signal_count=3,
                stage="closing",
            ),
        )
        assert len(captured_repo_calls) == 1
        kwargs = captured_repo_calls[0]
        assert kwargs["event_type"] == "domain_event"
        assert kwargs["name"] == "LeadQualified"
        assert kwargs["lead_id"] == lead_id
        assert kwargs["tenant_id"] == tenant_id
        assert kwargs["data"]["lead_score"] == 85
        assert kwargs["data"]["stage"] == "closing"


class TestToolLoopDetectedSubscriber:
    @pytest.mark.asyncio
    async def test_persists_with_error_status(self, captured_repo_calls: list[dict]) -> None:
        from src.modules.sales_agent.domain.events import ToolLoopDetectedEvent
        from src.modules.sales_agent.observability.domain_events.subscribers import (
            on_tool_loop_detected,
        )

        await on_tool_loop_detected(
            ToolLoopDetectedEvent(
                tenant_id=uuid4(),
                lead_id=uuid4(),
                channel_type="whatsapp",
                turn_id=uuid4(),
                tool_name="create_payment_link",
                repeat_count=5,
                args_hash="abc1234",
            ),
        )
        assert len(captured_repo_calls) == 1
        assert captured_repo_calls[0]["status"] == "error"
        assert captured_repo_calls[0]["data"]["tool_name"] == "create_payment_link"


class TestSubscriberIsBestEffort:
    @pytest.mark.asyncio
    async def test_repo_failure_does_not_propagate(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        class _BoomRepo:
            def __init__(self, db: object) -> None: ...

            def add(self, **_: object) -> None:
                msg = "DB exploded"
                raise RuntimeError(msg)

        monkeypatch.setattr(
            "src.modules.sales_agent.observability.domain_events.subscribers.SalesAgentTraceEventRepository",
            _BoomRepo,
        )

        from src.modules.sales_agent.domain.events import StageTransitionedEvent
        from src.modules.sales_agent.observability.domain_events.subscribers import (
            on_stage_transitioned,
        )

        # Must not raise.
        await on_stage_transitioned(
            StageTransitionedEvent(
                tenant_id=uuid4(),
                lead_id=uuid4(),
                channel_type="web",
                turn_id=uuid4(),
                from_stage="rapport",
                to_stage="discovery",
                lead_score=20,
            ),
        )


class TestRegisterSubscribers:
    def test_register_subscribers_wires_all_four_handlers(self) -> None:
        from src.modules.sales_agent.application.event_bus import EventBus
        from src.modules.sales_agent.domain.events import (
            LeadQualifiedEvent,
            ObjectionHandledEvent,
            StageTransitionedEvent,
            ToolLoopDetectedEvent,
        )
        from src.modules.sales_agent.observability.domain_events.subscribers import (
            register_subscribers,
        )

        bus = EventBus()
        register_subscribers(bus)

        # Inspect private subscribers dict — wiring smoke.
        subs = bus._subscribers
        for evt_cls in (
            LeadQualifiedEvent,
            ObjectionHandledEvent,
            StageTransitionedEvent,
            ToolLoopDetectedEvent,
        ):
            assert evt_cls in subs
            assert len(subs[evt_cls]) == 1
