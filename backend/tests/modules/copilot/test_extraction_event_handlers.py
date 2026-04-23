"""TDD: copilot extraction event handlers — Phase 2 BE refactor.

Tests verify that:
1. EventBus.publish(ExtractionSectionCompletedEvent) routes to the registered handler
   which calls the copilot emitter (navigation pill).
2. EventBus.publish(ExtractionJobCompletedEvent) routes to the registered handler
   which calls the copilot emitter (summary card).
3. register_extraction_event_handlers() is idempotent (safe to call twice).
4. Handlers are resilient — exceptions in emitter do not propagate.

All tests use mocked ConversationRepository and Redis — no real DB required.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.shared.domain.events import (
    EventBus,
    ExtractionJobCompletedEvent,
    ExtractionSectionCompletedEvent,
)

TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
CONVERSATION_ID = uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee")
JOB_ID = str(uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"))


@pytest.fixture(autouse=True)
def clear_event_bus() -> None:
    """Reset EventBus handlers before each test for isolation."""
    EventBus.clear()
    yield
    EventBus.clear()


class TestExtractionEventDefinitions:
    """Verify the two new event types exist and are well-formed."""

    def test_extraction_section_completed_event_create(self) -> None:
        """ExtractionSectionCompletedEvent.create() produces correct payload."""
        event = ExtractionSectionCompletedEvent.create(
            tenant_id=TENANT_ID,
            job_id=JOB_ID,
            conversation_id=str(CONVERSATION_ID),
            module="brand",
            section_slug="identity",
            section_label="Identidad",
            fields_count=5,
        )
        assert event.event_name == "extraction_section_completed"
        assert event.tenant_id == TENANT_ID
        assert event.payload["job_id"] == JOB_ID
        assert event.payload["conversation_id"] == str(CONVERSATION_ID)
        assert event.payload["module"] == "brand"
        assert event.payload["section_slug"] == "identity"
        assert event.payload["section_label"] == "Identidad"
        assert event.payload["fields_count"] == 5

    def test_extraction_job_completed_event_create(self) -> None:
        """ExtractionJobCompletedEvent.create() produces correct payload."""
        event = ExtractionJobCompletedEvent.create(
            tenant_id=TENANT_ID,
            job_id=JOB_ID,
            conversation_id=str(CONVERSATION_ID),
            module="brand",
            source_ref="https://visionarias.pe",
            duration_seconds=42,
            filled_fields=["brand_name", "tagline"],
            filled_fields_by_section={"identity": ["brand_name", "tagline"]},
            sections_completed=["identity"],
            primary_cta_route="/brand-studio/identity",
        )
        assert event.event_name == "extraction_job_completed"
        assert event.tenant_id == TENANT_ID
        assert event.payload["job_id"] == JOB_ID
        assert event.payload["module"] == "brand"
        assert event.payload["source_ref"] == "https://visionarias.pe"
        assert event.payload["duration_seconds"] == 42
        assert event.payload["filled_fields"] == ["brand_name", "tagline"]
        assert event.payload["sections_completed"] == ["identity"]

    def test_extraction_section_event_with_none_conversation(self) -> None:
        """conversation_id can be None (no conversation context)."""
        event = ExtractionSectionCompletedEvent.create(
            tenant_id=TENANT_ID,
            job_id=JOB_ID,
            conversation_id=None,
            module="offer",
            section_slug="promise",
            section_label="Promesa",
            fields_count=3,
        )
        assert event.payload["conversation_id"] is None

    def test_extraction_job_event_with_none_conversation(self) -> None:
        """conversation_id can be None in job-completed event."""
        event = ExtractionJobCompletedEvent.create(
            tenant_id=TENANT_ID,
            job_id=JOB_ID,
            conversation_id=None,
            module="offer",
            source_ref="documento",
            duration_seconds=30,
            filled_fields=[],
            filled_fields_by_section={},
            sections_completed=[],
            primary_cta_route=None,
        )
        assert event.payload["conversation_id"] is None


class TestRegisterExtractionEventHandlers:
    """Verify handler registration and idempotency."""

    def test_register_subscribes_both_events(self) -> None:
        """After register, EventBus has handlers for both extraction event names."""
        from src.modules.copilot.application.extraction_card_flow import (
            register_extraction_event_handlers,
        )

        register_extraction_event_handlers()

        assert "extraction_section_completed" in EventBus._handlers
        assert "extraction_job_completed" in EventBus._handlers
        assert len(EventBus._handlers["extraction_section_completed"]) >= 1
        assert len(EventBus._handlers["extraction_job_completed"]) >= 1

    def test_register_idempotent_no_duplicate_handlers(self) -> None:
        """Calling register twice does not duplicate handlers."""
        from src.modules.copilot.application.extraction_card_flow import (
            register_extraction_event_handlers,
        )

        register_extraction_event_handlers()
        count_section = len(EventBus._handlers.get("extraction_section_completed", []))
        count_job = len(EventBus._handlers.get("extraction_job_completed", []))

        register_extraction_event_handlers()

        # Handlers may grow if not guarded — test asserts the count stays the same
        assert len(EventBus._handlers["extraction_section_completed"]) == count_section
        assert len(EventBus._handlers["extraction_job_completed"]) == count_job


class TestHandlerResiliency:
    """Handlers must not propagate exceptions from the emitter."""

    def test_section_handler_swallows_emitter_exception(self) -> None:
        """If the emitter raises, the handler catches and logs — never re-raises."""
        from src.modules.copilot.application.extraction_card_flow import (
            handle_section_completed,
        )

        event = ExtractionSectionCompletedEvent.create(
            tenant_id=TENANT_ID,
            job_id=JOB_ID,
            conversation_id=str(CONVERSATION_ID),
            module="brand",
            section_slug="identity",
            section_label="Identidad",
            fields_count=5,
        )

        with (
            patch("src.core.database.SessionLocal", side_effect=RuntimeError("DB down")),
        ):
            # Must not raise
            handle_section_completed(event)

    def test_job_handler_swallows_emitter_exception(self) -> None:
        """If the emitter raises, the job handler catches and logs — never re-raises."""
        from src.modules.copilot.application.extraction_card_flow import (
            handle_job_completed,
        )

        event = ExtractionJobCompletedEvent.create(
            tenant_id=TENANT_ID,
            job_id=JOB_ID,
            conversation_id=str(CONVERSATION_ID),
            module="brand",
            source_ref="https://example.com",
            duration_seconds=10,
            filled_fields=[],
            filled_fields_by_section={},
            sections_completed=[],
            primary_cta_route=None,
        )

        with (
            patch("src.core.database.SessionLocal", side_effect=RuntimeError("DB down")),
        ):
            # Must not raise
            handle_job_completed(event)


class TestHandlerSkipsWhenNoConversation:
    """Handlers must be no-ops when conversation_id is None."""

    def test_section_handler_no_op_without_conversation(self) -> None:
        """If conversation_id is None, section handler does nothing."""
        from src.modules.copilot.application.extraction_card_flow import (
            handle_section_completed,
        )

        event = ExtractionSectionCompletedEvent.create(
            tenant_id=TENANT_ID,
            job_id=JOB_ID,
            conversation_id=None,
            module="brand",
            section_slug="identity",
            section_label="Identidad",
            fields_count=2,
        )

        db_mock = MagicMock()
        with patch("src.core.database.SessionLocal", return_value=db_mock):
            handle_section_completed(event)

        # SessionLocal should NOT be called — we exit before opening a session
        db_mock.close.assert_not_called()

    def test_job_handler_no_op_without_conversation(self) -> None:
        """If conversation_id is None, job handler does nothing."""
        from src.modules.copilot.application.extraction_card_flow import (
            handle_job_completed,
        )

        event = ExtractionJobCompletedEvent.create(
            tenant_id=TENANT_ID,
            job_id=JOB_ID,
            conversation_id=None,
            module="brand",
            source_ref="https://example.com",
            duration_seconds=10,
            filled_fields=[],
            filled_fields_by_section={},
            sections_completed=[],
            primary_cta_route=None,
        )

        db_mock = MagicMock()
        with patch("src.core.database.SessionLocal", return_value=db_mock):
            handle_job_completed(event)

        db_mock.close.assert_not_called()


class TestEventBusRouting:
    """Verify EventBus routes published events to registered handlers."""

    def test_publish_section_event_calls_handler(self) -> None:
        """EventBus.publish(ExtractionSectionCompletedEvent) calls the registered handler."""
        called_with: list[object] = []
        EventBus.subscribe("extraction_section_completed", called_with.append)

        event = ExtractionSectionCompletedEvent.create(
            tenant_id=TENANT_ID,
            job_id=JOB_ID,
            conversation_id=None,
            module="brand",
            section_slug="identity",
            section_label="Identidad",
            fields_count=3,
        )
        EventBus.publish(event, session=None)

        assert len(called_with) == 1
        assert called_with[0] is event

    def test_publish_job_event_calls_handler(self) -> None:
        """EventBus.publish(ExtractionJobCompletedEvent) calls the registered handler."""
        called_with: list[object] = []
        EventBus.subscribe("extraction_job_completed", called_with.append)

        event = ExtractionJobCompletedEvent.create(
            tenant_id=TENANT_ID,
            job_id=JOB_ID,
            conversation_id=None,
            module="offer",
            source_ref="documento",
            duration_seconds=20,
            filled_fields=[],
            filled_fields_by_section={},
            sections_completed=[],
            primary_cta_route=None,
        )
        EventBus.publish(event, session=None)

        assert len(called_with) == 1
        assert called_with[0] is event


class TestEmitterFunctions:
    """Verify the relocated copilot emitter functions work correctly."""

    def test_emit_section_pill_inserts_navigation_card(self) -> None:
        """emit_section_complete_pill inserts a navigation card into the conversation."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_section_complete_pill,
        )

        appended_messages: list[dict] = []
        conv_repo_mock = MagicMock()
        conv_repo_mock.append_messages = MagicMock(
            side_effect=lambda conv_id, tenant_id, msgs, **kw: appended_messages.extend(msgs)
        )

        with (
            patch("src.core.database.redis_client", None),
            patch(
                "src.modules.copilot.application.extraction_card_flow.ConversationRepository",
                return_value=conv_repo_mock,
            ),
        ):
            emit_section_complete_pill(
                db=MagicMock(),
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=str(uuid.uuid4()),
                section_slug="identity",
                section_label="Identidad",
                fields_count=5,
                module="brand",
            )

        assert len(appended_messages) == 1
        msg = appended_messages[0]
        assert "blocks" in msg
        assert msg["blocks"][0]["card_kind"] == "navigation"

    def test_emit_summary_card_inserts_extraction_summary(self) -> None:
        """emit_extraction_summary_card inserts an extraction_summary card."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_extraction_summary_card,
        )

        appended_messages: list[dict] = []
        conv_repo_mock = MagicMock()
        conv_repo_mock.append_messages = MagicMock(
            side_effect=lambda conv_id, tenant_id, msgs, **kw: appended_messages.extend(msgs)
        )

        unique_job_id = str(uuid.uuid4())
        with (
            patch("src.core.database.redis_client", None),
            patch(
                "src.modules.copilot.application.extraction_card_flow.ConversationRepository",
                return_value=conv_repo_mock,
            ),
        ):
            emit_extraction_summary_card(
                db=MagicMock(),
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=unique_job_id,
                source_ref="https://visionarias.pe",
                duration_seconds=38,
                filled_fields=["brand_name", "tagline"],
                filled_fields_by_section={"identity": ["brand_name", "tagline"]},
                sections_completed=["identity"],
            )

        assert len(appended_messages) == 1
        msg = appended_messages[0]
        assert msg["blocks"][0]["card_kind"] == "extraction_summary"

    def test_emit_section_pill_idempotent_with_redis(self) -> None:
        """Second call with same job_id+slug is a no-op when Redis returns a hit."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_section_complete_pill,
        )

        redis_mock = MagicMock()
        redis_mock.get = MagicMock(return_value=b"1")  # already emitted

        appended_messages: list[dict] = []
        conv_repo_mock = MagicMock()
        conv_repo_mock.append_messages = MagicMock(
            side_effect=lambda *a, **kw: appended_messages.extend(a[2] if len(a) > 2 else [])
        )

        with (
            patch("src.core.database.redis_client", redis_mock),
            patch(
                "src.modules.copilot.application.extraction_card_flow.ConversationRepository",
                return_value=conv_repo_mock,
            ),
        ):
            emit_section_complete_pill(
                db=MagicMock(),
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=JOB_ID,
                section_slug="identity",
                section_label="Identidad",
                fields_count=5,
                module="brand",
            )

        # No messages appended — idempotency guard fired
        assert len(appended_messages) == 0
