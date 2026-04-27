"""Tests for the copilot trace recorder.

Verifies that ``trace_recorder.start`` returns a working recorder that
persists rows into ``copilot_trace_event`` with the expected shape, and that
the ``span`` context manager captures duration + error status.

Uses ``monkeypatch`` to intercept ``SessionLocal`` so tests don't touch the
real DB: they assert what the recorder *would* have written, which is what
matters for contract stability.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import pytest

from src.modules.copilot.application.observability import trace_recorder

if TYPE_CHECKING:
    from unittest.mock import MagicMock


@pytest.fixture
def capturing_session(monkeypatch: pytest.MonkeyPatch) -> list[SimpleNamespace]:
    """Capture every row the recorder adds through its session factory.

    Both the session AND the ORM model are stubbed: the model is replaced
    with a lightweight ``SimpleNamespace`` factory so SQLAlchemy's global
    mapper configuration (which may fail in isolated unit tests when
    unrelated mappers reference each other) never runs during recording.

    Usa ``set_session_factory`` (API pluggable expuesta por el módulo) en
    lugar de monkeypatchear el viejo binding ``SessionLocal`` — el recorder
    ahora resuelve la sesión via ``_session_factory()`` para soportar
    inyección desde tests sin tocar el comportamiento de PROD. Esto
    además override el autouse ``_isolate_trace_recorder_db`` del root
    conftest que setea un no-op factory por default.
    """
    captured: list[SimpleNamespace] = []

    class _StubSession:
        def __init__(self) -> None:
            self.added: SimpleNamespace | None = None

        def add(self, obj: SimpleNamespace) -> None:
            self.added = obj
            captured.append(obj)

        def commit(self) -> None:
            return None

        def rollback(self) -> None:
            return None

        def close(self) -> None:
            return None

    def _fake_model(**kwargs: object) -> SimpleNamespace:
        return SimpleNamespace(**kwargs)

    trace_recorder.set_session_factory(_StubSession)
    monkeypatch.setattr(trace_recorder, "CopilotTraceEventModel", _fake_model)
    yield captured
    trace_recorder.reset_session_factory()


class TestTraceRecorder:
    def test_start_with_tenant_returns_real_recorder(self) -> None:
        tenant = uuid4()
        rec = trace_recorder.start(tenant_id=tenant)
        assert isinstance(rec, trace_recorder.TraceRecorder)
        assert rec.tenant_id == tenant

    def test_start_without_tenant_returns_noop(self) -> None:
        rec = trace_recorder.start(tenant_id=None)
        # Noop still satisfies the interface contract.
        assert hasattr(rec, "record")
        assert hasattr(rec, "span")

    def test_record_writes_row_with_core_fields(
        self,
        capturing_session: list[MagicMock],
    ) -> None:
        rec = trace_recorder.start(
            tenant_id=uuid4(),
            user_id=uuid4(),
            conversation_id=uuid4(),
        )
        returned = rec.record(
            event_type="llm_call",
            name="agent_node",
            data={"model": "gpt-4o", "prompt_tokens": 5000},
        )

        assert len(capturing_session) == 1
        row = capturing_session[0]
        assert row.event_type == "llm_call"
        assert row.name == "agent_node"
        assert row.data == {"model": "gpt-4o", "prompt_tokens": 5000}
        assert row.status == "ok"
        assert row.span_id == returned

    def test_record_truncates_long_strings_in_data(
        self,
        capturing_session: list[MagicMock],
    ) -> None:
        rec = trace_recorder.start(tenant_id=uuid4())
        huge = "x" * (trace_recorder.MAX_PAYLOAD_CHARS + 500)
        rec.record(event_type="tool_call", name="extract_from_url", data={"args": huge})

        row = capturing_session[0]
        stored = row.data["args"]
        assert isinstance(stored, str)
        assert len(stored) <= trace_recorder.MAX_PAYLOAD_CHARS + 30
        assert stored.endswith("[truncated]")

    def test_span_context_records_duration_and_ok_on_success(
        self,
        capturing_session: list[MagicMock],
    ) -> None:
        rec = trace_recorder.start(tenant_id=uuid4())
        with rec.span(event_type="node_exit", name="agent"):
            # Very short block — duration_ms is still non-negative.
            pass

        assert len(capturing_session) == 1
        row = capturing_session[0]
        assert row.status == "ok"
        assert row.duration_ms is not None
        assert row.duration_ms >= 0

    def test_span_context_records_error_and_reraises(
        self,
        capturing_session: list[MagicMock],
    ) -> None:
        rec = trace_recorder.start(tenant_id=uuid4())
        boom_msg = "boom"
        with (
            pytest.raises(RuntimeError, match=boom_msg),
            rec.span(event_type="tool_call", name="extract_from_url"),
        ):
            raise RuntimeError(boom_msg)

        assert len(capturing_session) == 1
        row = capturing_session[0]
        assert row.status == "error"
        assert row.data["error_type"] == "RuntimeError"
        assert row.data["error_message"] == "boom"

    def test_parent_span_id_is_preserved(
        self,
        capturing_session: list[MagicMock],
    ) -> None:
        rec = trace_recorder.start(tenant_id=uuid4())
        parent = uuid4()
        rec.record(event_type="tool_call", name="clarify", parent_span_id=parent)

        row = capturing_session[0]
        assert row.parent_span_id == parent

    def test_noop_recorder_never_writes(
        self,
        capturing_session: list[MagicMock],
    ) -> None:
        rec = trace_recorder.start(tenant_id=None)
        result_id = rec.record(event_type="llm_call", name="agent")
        assert len(capturing_session) == 0
        assert isinstance(result_id, UUID)

    def test_write_failure_is_swallowed(self) -> None:
        """Any DB failure must NOT propagate out of ``record``."""
        failure_msg = "disk on fire"

        class _FailingSession:
            def add(self, _obj: object) -> None:
                return None

            def commit(self) -> None:
                raise RuntimeError(failure_msg)

            def rollback(self) -> None:
                return None

            def close(self) -> None:
                return None

        trace_recorder.set_session_factory(_FailingSession)
        try:
            rec = trace_recorder.start(tenant_id=uuid4())
            # Must not raise — observability is best-effort.
            rec.record(event_type="tool_call", name="x")
        finally:
            trace_recorder.reset_session_factory()


class TestSanitizePayload:
    def test_noop_for_small_values(self) -> None:
        out = trace_recorder._sanitize_payload({"a": 1, "b": "short"})
        assert out == {"a": 1, "b": "short"}

    def test_truncates_long_string(self) -> None:
        huge = "y" * (trace_recorder.MAX_PAYLOAD_CHARS + 10)
        out = trace_recorder._sanitize_payload({"output": huge})
        assert out["output"].endswith("[truncated]")

    def test_empty_payload(self) -> None:
        assert trace_recorder._sanitize_payload({}) == {}
        # None is normalized to empty dict at recorder level; sanitize handles dict only.
        assert trace_recorder._sanitize_payload(SimpleNamespace() and {}) == {}
