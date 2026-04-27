"""Tests for the turn envelope (``ObservabilityContext``).

Verifies the public contract that chat.py will rely on at the Phase 2
atomic switch:

* ``ObservabilityContext.start(...)`` returns a ready context — turn_id
  is allocated.
* ``langchain_config()`` returns a dict with ``callbacks=[handler]``
  suitable for ``RunnableConfig``.
* ``async with`` opens a turn_start row and closes a turn_end row with
  totals computed from llm_call rows for the turn.
* Exceptions inside the ``async with`` body still close the turn (no
  row leak).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _build_context(db):
    """Helper that wires the new envelope to an in-memory SQLite session."""
    from src.modules.copilot.observability.persistence.llm_call_repository import LlmCallRepository
    from src.modules.copilot.observability.persistence.trace_event_repository import (
        TraceEventRepository,
    )
    from src.modules.copilot.observability.recording.turn_envelope import ObservabilityContext

    pricing_resolver = MagicMock()
    fx_resolver = MagicMock()
    fx_resolver.resolve.return_value = (Decimal(1), "passthrough")

    return ObservabilityContext.start(
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        user_id=uuid4(),
        llm_call_repo=LlmCallRepository(db),
        trace_repo=TraceEventRepository(db),
        pricing_resolver=pricing_resolver,
        fx_resolver=fx_resolver,
        tenant_currency="USD",
        role="agent",
    )


class TestEnvelopePublicAPI:
    def test_start_allocates_turn_id(self, db) -> None:
        ctx = _build_context(db)
        assert ctx.turn_id is not None
        assert ctx.callback_handler is not None

    def test_langchain_config_returns_dict_with_callbacks(self, db) -> None:
        ctx = _build_context(db)
        config = ctx.langchain_config()
        assert "callbacks" in config
        assert ctx.callback_handler in config["callbacks"]


class TestEnvelopeLifecycle:
    @pytest.mark.asyncio
    async def test_aenter_writes_turn_start(self, db) -> None:
        from src.modules.copilot.infrastructure.models.trace_event_model import (
            CopilotTraceEventModel,
        )

        ctx = _build_context(db)
        async with ctx.observe_turn(
            message="hola",
            route="/copilot/chat",
            attachments=[],
        ):
            db.flush()
            row = db.query(CopilotTraceEventModel).filter_by(turn_id=ctx.turn_id, event_type="turn_start").one()
            assert row.status == "ok"
            assert row.name == "/copilot/chat"

    @pytest.mark.asyncio
    async def test_aexit_writes_turn_end_with_totals(self, db) -> None:
        from src.modules.copilot.infrastructure.models.trace_event_model import (
            CopilotTraceEventModel,
        )
        from src.modules.copilot.observability.persistence.models.llm_call_model import (
            CopilotLlmCallModel,
        )

        ctx = _build_context(db)
        async with ctx.observe_turn(message="hola", route="/copilot/chat", attachments=[]):
            # Simulate two LLM calls landing during the turn.
            for i in range(2):
                db.add(
                    CopilotLlmCallModel(
                        tenant_id=ctx.tenant_id,
                        turn_id=ctx.turn_id,
                        span_id=uuid4(),
                        role="agent",
                        provider="openai",
                        model_requested="gpt-4o",
                        model_responded="gpt-4o-2024-11-20",
                        input_tokens=100 * (i + 1),
                        output_tokens=50 * (i + 1),
                        cached_read_tokens=0,
                        cached_write_tokens=0,
                        reasoning_tokens=0,
                        pricing_version_id=uuid4(),
                        input_unit_cost_usd=Decimal("0.0000025"),
                        output_unit_cost_usd=Decimal("0.000010"),
                        cached_read_unit_cost_usd=Decimal(0),
                        cost_usd=Decimal("0.001") * (i + 1),
                        tenant_currency="USD",
                        fx_rate_to_tenant=Decimal(1),
                        fx_rate_source="passthrough",
                        cost_tenant_currency=Decimal("0.001") * (i + 1),
                        started_at=dt.datetime.now(tz=dt.UTC),
                        duration_ms=200,
                        status="ok",
                    ),
                )
            db.flush()
        db.flush()

        end_row = db.query(CopilotTraceEventModel).filter_by(turn_id=ctx.turn_id, event_type="turn_end").one()
        # Totals are computed from copilot_llm_call rows.
        assert end_row.data["llm_call_count"] == 2
        assert end_row.data["total_input_tokens"] == 300
        assert end_row.data["total_output_tokens"] == 150
        # cost_usd = 0.001 + 0.002 = 0.003
        assert Decimal(end_row.data["total_cost_usd"]) == Decimal("0.003")

    @pytest.mark.asyncio
    async def test_aexit_writes_turn_end_with_error_status_on_exception(self, db) -> None:
        from src.modules.copilot.infrastructure.models.trace_event_model import (
            CopilotTraceEventModel,
        )

        ctx = _build_context(db)
        with pytest.raises(RuntimeError):
            async with ctx.observe_turn(message="hola", route="/copilot/chat", attachments=[]):
                msg = "boom"
                raise RuntimeError(msg)
        db.flush()

        end_row = db.query(CopilotTraceEventModel).filter_by(turn_id=ctx.turn_id, event_type="turn_end").one()
        assert end_row.status == "error"
        assert "RuntimeError" in end_row.data.get("error_type", "")

    @pytest.mark.asyncio
    async def test_set_turn_error_marks_status_when_exception_swallowed(self, db) -> None:
        """Fix 5 — the orchestrator catches stream exceptions internally
        (TimeoutError, ToolCallLoopDetected, generic Exception) so the
        envelope sees no exception and marks the turn ``status='ok'``.
        That hid real failures (2026-04-27 incident: GraphRecursionError
        landed but turn_end said ``ok``).

        ``set_turn_error(error_kind, error_message)`` lets the orchestrator
        flag the turn from inside the except block. The envelope's finally
        path then writes ``status='error'`` plus the kind + message into
        the turn_end ``data`` payload.
        """
        from src.modules.copilot.infrastructure.models.trace_event_model import (
            CopilotTraceEventModel,
        )

        ctx = _build_context(db)
        async with ctx.observe_turn(
            message="hola",
            route="/copilot/chat",
            attachments=[],
        ):
            # Simulate the orchestrator catching a stream error and flagging
            # the turn before the context manager exits cleanly.
            ctx.set_turn_error(
                error_kind="graph_recursion",
                error_message="Recursion limit of 25 reached",
            )
        db.flush()

        end_row = db.query(CopilotTraceEventModel).filter_by(turn_id=ctx.turn_id, event_type="turn_end").one()
        assert end_row.status == "error"
        assert end_row.data.get("error_kind") == "graph_recursion"
        # Error message must reach the trace so debugging does not require
        # cross-referencing docker logs.
        assert "Recursion" in end_row.data.get("error_message", "")

    @pytest.mark.asyncio
    async def test_set_turn_error_takes_precedence_over_clean_exit(self, db) -> None:
        """Even when the body returns normally, an explicit set_turn_error
        flag must override the default ``ok`` status."""
        from src.modules.copilot.infrastructure.models.trace_event_model import (
            CopilotTraceEventModel,
        )

        ctx = _build_context(db)
        async with ctx.observe_turn(
            message="hola",
            route="/copilot/chat",
            attachments=[],
        ):
            ctx.set_turn_error(error_kind="tool_call_loop")
        db.flush()

        end_row = db.query(CopilotTraceEventModel).filter_by(turn_id=ctx.turn_id, event_type="turn_end").one()
        assert end_row.status == "error"
        assert end_row.data.get("error_kind") == "tool_call_loop"
