"""TDD — Observabilidad: extraction_card_flow debe grabar trace card_emitted.

Bug confirmado: emit_section_complete_pill() y emit_extraction_summary_card()
insertan cards en copilot_conversations.messages PERO no llaman al
trace_recorder, por lo que copilot_trace_event muestra 0 rows con
event_type='card_emitted' para navigation + extraction_summary cards.

Invariante:
  Cuando emit_section_complete_pill() inserta una nav pill con éxito,
  el trace_recorder debe recibir una llamada record(event_type="card_emitted",
  name="navigation", data incluyendo card_kind, conversation_id, job_id).

  Cuando emit_extraction_summary_card() inserta una summary card con éxito,
  el trace_recorder debe recibir record(event_type="card_emitted",
  name="extraction_summary", data incluyendo card_kind, job_id).
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
CONVERSATION_ID = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
JOB_ID = str(uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"))


class TestNavPillRecordsTrace:
    """emit_section_complete_pill must call trace_recorder with card_emitted."""

    def test_nav_pill_records_card_emitted_event(self) -> None:
        """On successful pill emit, trace_recorder.record called with card_emitted."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_section_complete_pill,
        )

        recorder = MagicMock()
        recorder.record = MagicMock(return_value=uuid.uuid4())

        conv_repo_mock = MagicMock()
        conv_repo_mock.append_messages = MagicMock()

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
                job_id=JOB_ID,
                section_slug="identity",
                section_label="Identidad",
                fields_count=5,
                module="brand",
                trace_recorder=recorder,
            )

        # trace_recorder.record must have been called
        recorder.record.assert_called_once()
        call_kwargs = recorder.record.call_args.kwargs
        assert call_kwargs.get("event_type") == "card_emitted", (
            f"Expected event_type='card_emitted', got {call_kwargs.get('event_type')!r}"
        )
        assert call_kwargs.get("name") == "navigation", f"Expected name='navigation', got {call_kwargs.get('name')!r}"
        data = call_kwargs.get("data", {})
        assert data.get("card_kind") == "navigation", (
            f"Expected data.card_kind='navigation', got {data.get('card_kind')!r}"
        )
        assert data.get("job_id") == JOB_ID
        assert data.get("conversation_id") == str(CONVERSATION_ID)

    def test_nav_pill_no_trace_when_recorder_none(self) -> None:
        """When trace_recorder=None (legacy call), no error raised."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_section_complete_pill,
        )

        conv_repo_mock = MagicMock()
        conv_repo_mock.append_messages = MagicMock()

        with (
            patch("src.core.database.redis_client", None),
            patch(
                "src.modules.copilot.application.extraction_card_flow.ConversationRepository",
                return_value=conv_repo_mock,
            ),
        ):
            # Should not raise even without trace_recorder
            emit_section_complete_pill(
                db=MagicMock(),
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=JOB_ID,
                section_slug="identity",
                section_label="Identidad",
                fields_count=3,
                module="brand",
                # trace_recorder not passed — defaults to None
            )

    def test_nav_pill_trace_not_called_on_duplicate(self) -> None:
        """When Redis guard fires (duplicate), trace_recorder.record is NOT called."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_section_complete_pill,
        )

        recorder = MagicMock()
        recorder.record = MagicMock(return_value=uuid.uuid4())

        redis_mock = MagicMock()
        redis_mock.get = MagicMock(return_value=b"1")  # already emitted

        with (
            patch("src.core.database.redis_client", redis_mock),
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
                trace_recorder=recorder,
            )

        # Redis guard fired → no card inserted → no trace record
        recorder.record.assert_not_called()

    def test_nav_pill_source_tool_in_trace_data(self) -> None:
        """Trace data must include source_tool='extract_from_url'."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_section_complete_pill,
        )

        recorder = MagicMock()
        recorder.record = MagicMock(return_value=uuid.uuid4())
        conv_repo_mock = MagicMock()
        conv_repo_mock.append_messages = MagicMock()

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
                job_id=JOB_ID,
                section_slug="story",
                section_label="Historia",
                fields_count=2,
                module="brand",
                trace_recorder=recorder,
            )

        data = recorder.record.call_args.kwargs.get("data", {})
        assert data.get("source_tool") == "extract_from_url", (
            f"Expected source_tool='extract_from_url', got {data.get('source_tool')!r}"
        )


class TestSummaryCardRecordsTrace:
    """emit_extraction_summary_card must call trace_recorder with card_emitted."""

    def test_summary_card_records_card_emitted_event(self) -> None:
        """On successful summary card emit, trace_recorder.record called with card_emitted."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_extraction_summary_card,
        )

        recorder = MagicMock()
        recorder.record = MagicMock(return_value=uuid.uuid4())

        conv_repo_mock = MagicMock()
        conv_repo_mock.append_messages = MagicMock()

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
                trace_recorder=recorder,
            )

        recorder.record.assert_called_once()
        call_kwargs = recorder.record.call_args.kwargs
        assert call_kwargs.get("event_type") == "card_emitted"
        assert call_kwargs.get("name") == "extraction_summary"
        data = call_kwargs.get("data", {})
        assert data.get("card_kind") == "extraction_summary"
        assert data.get("job_id") == unique_job_id

    def test_summary_card_no_trace_when_recorder_none(self) -> None:
        """No error when trace_recorder=None (backward compat)."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_extraction_summary_card,
        )

        conv_repo_mock = MagicMock()
        conv_repo_mock.append_messages = MagicMock()
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
                source_ref="https://example.com",
                duration_seconds=10,
                filled_fields=[],
                filled_fields_by_section={},
                sections_completed=[],
            )

    def test_summary_card_trace_not_called_on_duplicate(self) -> None:
        """Redis guard fires → no card inserted → no trace record."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_extraction_summary_card,
        )

        recorder = MagicMock()
        recorder.record = MagicMock(return_value=uuid.uuid4())

        redis_mock = MagicMock()
        redis_mock.get = MagicMock(return_value=b"1")  # already emitted

        with (
            patch("src.core.database.redis_client", redis_mock),
        ):
            emit_extraction_summary_card(
                db=MagicMock(),
                tenant_id=TENANT_ID,
                conversation_id=CONVERSATION_ID,
                job_id=JOB_ID,
                source_ref="https://example.com",
                duration_seconds=10,
                filled_fields=[],
                filled_fields_by_section={},
                sections_completed=[],
                trace_recorder=recorder,
            )

        recorder.record.assert_not_called()

    def test_summary_card_source_tool_in_trace_data(self) -> None:
        """Trace data must include source_tool='extract_from_url'."""
        from src.modules.copilot.application.extraction_card_flow import (
            emit_extraction_summary_card,
        )

        recorder = MagicMock()
        recorder.record = MagicMock(return_value=uuid.uuid4())
        conv_repo_mock = MagicMock()
        conv_repo_mock.append_messages = MagicMock()
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
                duration_seconds=10,
                filled_fields=["brand_name"],
                filled_fields_by_section={"identity": ["brand_name"]},
                sections_completed=["identity"],
                trace_recorder=recorder,
            )

        data = recorder.record.call_args.kwargs.get("data", {})
        assert data.get("source_tool") == "extract_from_url"


class TestHandlerPassesRecorderToEmitter:
    """handle_section_completed and handle_job_completed must pass recorder to emitters."""

    def test_handler_passes_recorder_context_to_pill_emitter(self) -> None:
        """handle_section_completed must create a recorder and pass it to emit_section_complete_pill."""
        from src.modules.copilot.application.extraction_card_flow import (
            handle_section_completed,
        )
        from src.shared.domain.events import ExtractionSectionCompletedEvent

        # We verify the recorder is created (TraceRecorder or _NoopRecorder)
        # by checking that trace_recorder module was used
        emitter_calls: list[dict] = []

        def capturing_emitter(**kwargs: object) -> None:
            emitter_calls.append(dict(kwargs))

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
            patch(
                "src.modules.copilot.application.extraction_card_flow.emit_section_complete_pill",
                side_effect=capturing_emitter,
            ),
            patch("src.core.database.SessionLocal", return_value=MagicMock()),
        ):
            handle_section_completed(event)

        assert len(emitter_calls) == 1
        # The handler must pass trace_recorder kwarg (may be None or a recorder instance)
        assert "trace_recorder" in emitter_calls[0], (
            "handler must forward trace_recorder= to emit_section_complete_pill"
        )

    def test_handler_passes_recorder_to_summary_emitter(self) -> None:
        """handle_job_completed must pass trace_recorder to emit_extraction_summary_card."""
        from src.modules.copilot.application.extraction_card_flow import (
            handle_job_completed,
        )
        from src.shared.domain.events import ExtractionJobCompletedEvent

        emitter_calls: list[dict] = []

        def capturing_emitter(**kwargs: object) -> None:
            emitter_calls.append(dict(kwargs))

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
            patch(
                "src.modules.copilot.application.extraction_card_flow.emit_extraction_summary_card",
                side_effect=capturing_emitter,
            ),
            patch("src.core.database.SessionLocal", return_value=MagicMock()),
        ):
            handle_job_completed(event)

        assert len(emitter_calls) == 1
        assert "trace_recorder" in emitter_calls[0], (
            "handler must forward trace_recorder= to emit_extraction_summary_card"
        )
