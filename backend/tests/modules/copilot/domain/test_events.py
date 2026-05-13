"""Tests for copilot domain events.

The events extend ``src.shared.domain.events.DomainEvent`` so the existing
``EventBus`` (string-keyed dispatch + after-commit semantics) handles them
uniformly with module-cross events.
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from luana_core_copilot.domain.events import (
    EVENT_CARD_EMITTED,
    EVENT_ROUTING_DECIDED,
    EVENT_TURN_ENDED,
    EVENT_TURN_STARTED,
    CardEmitted,
    RoutingDecided,
    TurnEnded,
    TurnStarted,
)
from luana_core_platform.domain.events import DomainEvent


class TestTurnStarted:
    def test_create_populates_event_name_and_payload(self) -> None:
        tenant = uuid4()
        turn = uuid4()
        conv = uuid4()
        user = uuid4()

        event = TurnStarted.create(
            tenant_id=tenant,
            user_id=user,
            conversation_id=conv,
            turn_id=turn,
            message_preview="hola",
            current_route="/brand-studio",
            guided_mode=True,
            attachment_count=2,
        )

        assert isinstance(event, DomainEvent)
        assert event.event_name == EVENT_TURN_STARTED
        assert event.tenant_id == tenant
        assert event.payload["turn_id"] == str(turn)
        assert event.payload["conversation_id"] == str(conv)
        assert event.payload["user_id"] == str(user)
        assert event.payload["message_preview"] == "hola"
        assert event.payload["current_route"] == "/brand-studio"
        assert event.payload["guided_mode"] is True
        assert event.payload["attachment_count"] == 2

    def test_create_defaults_when_optional_missing(self) -> None:
        event = TurnStarted.create(
            tenant_id=uuid4(),
            user_id=None,
            conversation_id=None,
            turn_id=uuid4(),
            message_preview="hi",
            current_route=None,
            guided_mode=False,
            attachment_count=0,
        )

        assert event.payload["conversation_id"] is None
        assert event.payload["user_id"] is None
        assert event.payload["current_route"] is None


class TestTurnEnded:
    def test_create_populates_event_name_and_payload(self) -> None:
        tenant = uuid4()
        turn = uuid4()

        event = TurnEnded.create(
            tenant_id=tenant,
            turn_id=turn,
            response_length=512,
            message_count=3,
            block_count=2,
            duration_ms=1234,
            error_type=None,
        )

        assert event.event_name == EVENT_TURN_ENDED
        assert event.payload["turn_id"] == str(turn)
        assert event.payload["response_length"] == 512
        assert event.payload["message_count"] == 3
        assert event.payload["block_count"] == 2
        assert event.payload["duration_ms"] == 1234
        assert event.payload["error_type"] is None

    def test_create_with_error(self) -> None:
        event = TurnEnded.create(
            tenant_id=uuid4(),
            turn_id=uuid4(),
            response_length=0,
            message_count=0,
            block_count=0,
            duration_ms=42,
            error_type="ValueError",
        )
        assert event.payload["error_type"] == "ValueError"


class TestCardEmitted:
    def test_create_populates_event_name_and_payload(self) -> None:
        tenant = uuid4()
        turn = uuid4()

        event = CardEmitted.create(
            tenant_id=tenant,
            turn_id=turn,
            conversation_id=None,
            card_kind="navigation",
            source_tool="extract_from_url",
            payload_keys=["route", "section_id"],
        )

        assert event.event_name == EVENT_CARD_EMITTED
        assert event.payload["turn_id"] == str(turn)
        assert event.payload["card_kind"] == "navigation"
        assert event.payload["source_tool"] == "extract_from_url"
        assert event.payload["payload_keys"] == ["route", "section_id"]

    def test_create_supports_optional_conversation_id(self) -> None:
        conv = uuid4()
        event = CardEmitted.create(
            tenant_id=uuid4(),
            turn_id=uuid4(),
            conversation_id=conv,
            card_kind="extraction_summary",
            source_tool="extraction_worker",
            payload_keys=[],
        )
        assert event.payload["conversation_id"] == str(conv)


class TestRoutingDecided:
    def test_create_populates_event_name_and_payload(self) -> None:
        tenant = uuid4()
        conv = uuid4()
        msg = uuid4()

        event = RoutingDecided.create(
            tenant_id=tenant,
            conversation_id=conv,
            message_id=msg,
            role_selected="agent",
            classifier_used="rule",
            reason="long_message",
            confidence=Decimal("0.85"),
            user_msg_length=120,
            tools_available=8,
        )

        assert event.event_name == EVENT_ROUTING_DECIDED
        assert event.payload["conversation_id"] == str(conv)
        assert event.payload["message_id"] == str(msg)
        assert event.payload["role"] == "agent"
        assert event.payload["classifier"] == "rule"
        assert event.payload["reason"] == "long_message"
        assert event.payload["confidence"] == "0.85"
        assert event.payload["user_msg_length"] == 120
        assert event.payload["tools_available"] == 8

    def test_create_serialises_none_confidence(self) -> None:
        event = RoutingDecided.create(
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            message_id=uuid4(),
            role_selected="nano",
            classifier_used="llm",
            reason="ambiguous",
            confidence=None,
            user_msg_length=10,
            tools_available=2,
        )
        assert event.payload["confidence"] is None


class TestEventConstants:
    def test_event_names_are_unique_and_namespaced(self) -> None:
        names = {EVENT_TURN_STARTED, EVENT_TURN_ENDED, EVENT_CARD_EMITTED, EVENT_ROUTING_DECIDED}
        assert len(names) == 4
        for name in names:
            assert name.startswith("copilot_")


@pytest.mark.parametrize(
    ("factory", "kwargs", "expected_name"),
    [
        (
            TurnStarted.create,
            {
                "tenant_id": uuid4(),
                "user_id": None,
                "conversation_id": None,
                "turn_id": uuid4(),
                "message_preview": "x",
                "current_route": None,
                "guided_mode": False,
                "attachment_count": 0,
            },
            EVENT_TURN_STARTED,
        ),
        (
            TurnEnded.create,
            {
                "tenant_id": uuid4(),
                "turn_id": uuid4(),
                "response_length": 0,
                "message_count": 0,
                "block_count": 0,
                "duration_ms": 0,
                "error_type": None,
            },
            EVENT_TURN_ENDED,
        ),
    ],
)
def test_factory_returns_domain_event_subclass(factory, kwargs, expected_name) -> None:
    event = factory(**kwargs)
    assert isinstance(event, DomainEvent)
    assert event.event_name == expected_name
