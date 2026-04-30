"""Test the module-level ``register()`` hook.

Phase 2 wires copilot observability into the FastAPI startup via a single
``register()`` call. The function is idempotent (re-registering doesn't
duplicate handlers) and best-effort (a publisher with no subscribers is a
no-op, never raises).
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.modules.copilot.domain.events import (
    EVENT_CARD_EMITTED,
    EVENT_ROUTING_DECIDED,
    EVENT_TURN_ENDED,
    EVENT_TURN_STARTED,
    CardEmitted,
    RoutingDecided,
    TurnEnded,
    TurnStarted,
)
from src.shared.domain.events import EventBus


@pytest.fixture(autouse=True)
def _clean_event_bus() -> None:
    """Avoid handler bleed across tests."""
    EventBus.clear()
    yield
    EventBus.clear()


@pytest.fixture
def fake_repo_factory() -> MagicMock:
    """Build a factory whose repos record `add` calls without touching the DB."""
    repo = MagicMock()
    repo.db = MagicMock()
    repo.db.commit = MagicMock()
    factory = MagicMock(return_value=repo)
    return factory


def test_register_subscribes_card_and_routing_events(fake_repo_factory) -> None:
    """Phase 2: turn_started / turn_ended are written by ObservabilityContext
    directly (single writer, owns the LLM-call aggregation). Subscribers
    cover card emissions + routing decisions only.
    """
    from src.modules.copilot.observability import register

    register(repo_factory=fake_repo_factory)

    handlers = EventBus._handlers
    assert handlers.get(EVENT_CARD_EMITTED), "no subscriber for card_emitted"
    assert handlers.get(EVENT_ROUTING_DECIDED), "no subscriber for routing_decided"
    assert not handlers.get(EVENT_TURN_STARTED), (
        "turn_started must NOT have a subscriber — observe_turn writes it directly"
    )
    assert not handlers.get(EVENT_TURN_ENDED), "turn_ended must NOT have a subscriber — observe_turn writes it directly"


def test_register_is_idempotent(fake_repo_factory) -> None:
    from src.modules.copilot.observability import register

    register(repo_factory=fake_repo_factory)
    first = {name: list(handlers) for name, handlers in EventBus._handlers.items()}

    register(repo_factory=fake_repo_factory)

    for name, before in first.items():
        after = EventBus._handlers.get(name, [])
        assert len(after) == len(before), f"{name} doubled on second register"


def test_register_persists_card_emitted_via_repo(fake_repo_factory) -> None:
    from src.modules.copilot.observability import register

    register(repo_factory=fake_repo_factory)

    event = CardEmitted.create(
        tenant_id=uuid4(),
        turn_id=uuid4(),
        conversation_id=uuid4(),
        card_kind="navigation",
        source_tool="extract_from_url",
        payload_keys=["route", "section_id"],
    )
    EventBus.publish(event, session=None)

    fake_repo_factory.assert_called()
    repo = fake_repo_factory.return_value
    repo.add.assert_called_once()


def test_register_does_not_persist_turn_events(fake_repo_factory) -> None:
    """Turn events bypass subscribers — observe_turn writes the rows."""
    from src.modules.copilot.observability import register

    register(repo_factory=fake_repo_factory)

    started = TurnStarted.create(
        tenant_id=uuid4(),
        user_id=uuid4(),
        conversation_id=uuid4(),
        turn_id=uuid4(),
        message_preview="hola",
        current_route=None,
        guided_mode=False,
        attachment_count=0,
    )
    EventBus.publish(started, session=None)

    ended = TurnEnded.create(
        tenant_id=uuid4(),
        turn_id=uuid4(),
        response_length=128,
        message_count=2,
        block_count=1,
        duration_ms=900,
        error_type=None,
    )
    EventBus.publish(ended, session=None)

    repo = fake_repo_factory.return_value
    assert repo.add.call_count == 0, "subscribers must not write turn_start/turn_end — observe_turn does it"


def test_register_persists_routing_decided(fake_repo_factory) -> None:
    from src.modules.copilot.observability import register

    register(repo_factory=fake_repo_factory)

    event = RoutingDecided.create(
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        message_id=uuid4(),
        role_selected="agent",
        classifier_used="rule",
        reason="x",
        confidence=None,
        user_msg_length=15,
        tools_available=4,
    )
    EventBus.publish(event, session=None)

    repo = fake_repo_factory.return_value
    repo.add.assert_called_once()


def test_register_repo_failure_does_not_propagate(fake_repo_factory) -> None:
    """Best-effort: a repo that raises on add MUST NOT bubble out of publish()."""
    from src.modules.copilot.observability import register

    repo = fake_repo_factory.return_value
    repo.add.side_effect = RuntimeError("DB exploded")

    register(repo_factory=fake_repo_factory)

    event = CardEmitted.create(
        tenant_id=uuid4(),
        turn_id=uuid4(),
        conversation_id=None,
        card_kind="x",
        source_tool="y",
        payload_keys=[],
    )
    # Must not raise.
    EventBus.publish(event, session=None)
