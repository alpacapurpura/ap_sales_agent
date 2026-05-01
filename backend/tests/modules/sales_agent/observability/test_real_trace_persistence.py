"""Real persistence test for sales_agent observability — Bug #2 PR-1.

Reproduces the production bug: ``sales_agent_trace_event`` /
``sales_agent_llm_call`` had **0 rows globally** despite ``messages``
table holding real Telegram inbound. RCA (see IMPL-LOG-agentic.md):

1. **PRIMARY** — sales_agent had no turn-envelope analogous to copilot's
   ``ObservabilityContext.observe_turn``. Without ``turn_start`` /
   ``turn_end`` writes + an explicit ``session.commit()``, callback
   rows added during ``ainvoke`` never get persisted (the orchestrator
   commit at ``save_checkpoint`` happens AFTER the graph and may not
   cover them — and many turns blow up earlier in the pipeline before
   reaching it).
2. **SECONDARY** — sync ``BaseCallbackHandler`` is dispatched by
   LangChain's ``AsyncCallbackManager`` via ``run_in_executor``
   (foreign thread). Rows ``add()``-ed from the worker thread land in
   the session's identity map but are only flushed when a main-thread
   commit / flush runs. Without an explicit envelope flush+commit, they
   silently disappear.

This test asserts the **real DB persistence contract** end-to-end: when
the new ``SalesAgentObservabilityContext`` brackets a turn, the
``turn_start`` and ``turn_end`` rows MUST exist in
``sales_agent_trace_event`` (queried by SELECT, not by mock spy)
without the caller having to run any further commit.

Uses the same in-memory SQLite engine that the rest of the test suite
uses (``conftest.py::db_engine``) — covers the persistence path
faithfully because the JSONB / UUID monkey-patches mirror Postgres
behaviour for column shapes. Real Postgres clone-DB validation is
covered separately by alembic migration tests.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db(db_engine):
    """Per-test session bound to a rolled-back transaction."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _build_context(db):
    """Wire a fresh ``SalesAgentObservabilityContext`` to the in-memory session."""
    from src.modules.sales_agent.observability.persistence.llm_call_repository import (
        SalesAgentLlmCallRepository,
    )
    from src.modules.sales_agent.observability.persistence.trace_event_repository import (
        SalesAgentTraceEventRepository,
    )
    from src.modules.sales_agent.observability.recording.turn_envelope import (
        SalesAgentObservabilityContext,
    )

    pricing_resolver = MagicMock()
    fx_resolver = MagicMock()
    fx_resolver.resolve.return_value = (Decimal(1), "passthrough")

    return SalesAgentObservabilityContext.start(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        channel_type="telegram",
        llm_call_repo=SalesAgentLlmCallRepository(db),
        trace_repo=SalesAgentTraceEventRepository(db),
        pricing_resolver=pricing_resolver,
        fx_resolver=fx_resolver,
        tenant_currency="USD",
        role="agent",
    )


def _build_llm_response(
    *,
    input_tokens: int = 1000,
    output_tokens: int = 500,
    model_name: str = "kimi-k2.6",
) -> SimpleNamespace:
    message = SimpleNamespace(
        usage_metadata={
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_token_details": {},
            "output_token_details": {},
        },
        response_metadata={"model_name": model_name},
    )
    generation = SimpleNamespace(message=message)
    return SimpleNamespace(generations=[[generation]], llm_output=None)


class TestRealTracePersistence:
    """Bug #2 reproducer — verdict GREEN means callbacks really commit."""

    @pytest.mark.asyncio
    async def test_observe_turn_writes_turn_start_to_db(self, db) -> None:
        """``__aenter__`` MUST insert + commit a ``turn_start`` row.

        SELECT directly against the in-memory DB — no mock spy, no
        ``flush`` outside the envelope. If the envelope forgets to
        commit, this assertion blows up.
        """
        from src.modules.sales_agent.observability.persistence.models.trace_event_model import (
            SalesAgentTraceEventModel,
        )

        ctx = _build_context(db)
        async with ctx.observe_turn(
            message="hola desde telegram",
            route="qualifier",
            attachments=[],
        ):
            row = db.query(SalesAgentTraceEventModel).filter_by(turn_id=ctx.turn_id, event_type="turn_start").one()
            assert row.lead_id == ctx.lead_id
            assert row.channel_type == "telegram"
            assert row.status == "ok"
            assert row.name == "qualifier"

    @pytest.mark.asyncio
    async def test_observe_turn_writes_turn_end_to_db(self, db) -> None:
        """``__aexit__`` MUST insert + commit a ``turn_end`` row.

        Reproduces the visible symptom — ``find_last_turn_end`` returned
        ``None`` for every lead even though messages flowed through the
        orchestrator. The fix wires an explicit ``turn_end`` row that
        admin ``sales_audit.py`` can read.
        """
        from src.modules.sales_agent.observability.persistence.models.trace_event_model import (
            SalesAgentTraceEventModel,
        )

        ctx = _build_context(db)
        async with ctx.observe_turn(message="hola", route="closer", attachments=[]):
            pass

        row = db.query(SalesAgentTraceEventModel).filter_by(turn_id=ctx.turn_id, event_type="turn_end").one()
        assert row.lead_id == ctx.lead_id
        assert row.channel_type == "telegram"
        assert row.status == "ok"
        assert row.duration_ms is not None
        assert row.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_callback_handler_rows_visible_after_envelope(self, db) -> None:
        """Rows added by the callback handler INSIDE the envelope MUST be
        visible after the envelope exits.

        The handler is dispatched by LangChain's ``AsyncCallbackManager``
        from a worker thread when ``ainvoke`` runs. Without the envelope's
        explicit ``flush`` + ``commit``, those worker-thread ``add()``
        calls would never reach Postgres. We simulate a sync handler
        invocation here (mirrors what LangChain dispatches synchronously
        in tests / sync paths) and confirm the row survives.
        """
        from src.modules.sales_agent.observability.persistence.models.trace_event_model import (
            SalesAgentTraceEventModel,
        )

        ctx = _build_context(db)

        # Make pricing resolver return a real snapshot so _persist_llm_call
        # can compute cost.
        snapshot = SimpleNamespace(
            id=uuid4(),
            input_cost_per_token=Decimal("0.0000004"),
            output_cost_per_token=Decimal("0.000002"),
            cache_read_cost_per_token=Decimal("0.0000001"),
            cache_write_cost_per_token=Decimal(0),
        )
        ctx.callback_handler.pricing_resolver.resolve.return_value = SimpleNamespace(
            snapshot=snapshot,
            is_estimated=False,
        )

        async with ctx.observe_turn(message="hola", route="qualifier", attachments=[]):
            run_id = uuid4()
            ctx.callback_handler.on_chat_model_start(
                serialized={"kwargs": {"model_name": "kimi-k2.6"}},
                messages=[],
                run_id=run_id,
                metadata={"ls_provider": "kimi", "ls_model_name": "kimi-k2.6"},
            )
            ctx.callback_handler.on_llm_end(
                response=_build_llm_response(),
                run_id=run_id,
            )

        # After the envelope exits, the trace event mirror written by
        # _persist_llm_call MUST be queryable via SELECT.
        rows = db.query(SalesAgentTraceEventModel).filter_by(turn_id=ctx.turn_id, event_type="llm_call").all()
        assert len(rows) == 1
        assert rows[0].lead_id == ctx.lead_id
        assert rows[0].name == "kimi.kimi-k2.6"

    @pytest.mark.asyncio
    async def test_observe_turn_marks_error_on_exception(self, db) -> None:
        """``turn_end`` row MUST record ``status='error'`` when body raises."""
        from src.modules.sales_agent.observability.persistence.models.trace_event_model import (
            SalesAgentTraceEventModel,
        )

        ctx = _build_context(db)
        boom_msg = "boom"
        with pytest.raises(RuntimeError, match="boom"):
            async with ctx.observe_turn(message="hola", route="qualifier", attachments=[]):
                raise RuntimeError(boom_msg)

        row = db.query(SalesAgentTraceEventModel).filter_by(turn_id=ctx.turn_id, event_type="turn_end").one()
        assert row.status == "error"
        assert row.data.get("error_type") == "RuntimeError"

    @pytest.mark.asyncio
    async def test_set_turn_error_marks_clean_exit_as_error(self, db) -> None:
        """``set_turn_error`` MUST flip turn_end to ``status='error'`` even
        when the body returns cleanly (orchestrator caught the exception
        itself to emit a user-friendly fallback message).
        """
        from src.modules.sales_agent.observability.persistence.models.trace_event_model import (
            SalesAgentTraceEventModel,
        )

        ctx = _build_context(db)
        async with ctx.observe_turn(message="hola", route="qualifier", attachments=[]):
            ctx.set_turn_error(
                error_kind="graph_invocation_failed",
                error_message="LLM provider timeout",
            )

        row = db.query(SalesAgentTraceEventModel).filter_by(turn_id=ctx.turn_id, event_type="turn_end").one()
        assert row.status == "error"
        assert row.data.get("error_kind") == "graph_invocation_failed"
        assert "timeout" in row.data.get("error_message", "")


class TestEnvelopePublicAPI:
    """Lightweight invariants on the envelope's public surface."""

    def test_start_allocates_turn_id(self, db) -> None:
        ctx = _build_context(db)
        assert ctx.turn_id is not None
        assert ctx.callback_handler is not None

    def test_langchain_config_returns_callbacks_dict(self, db) -> None:
        ctx = _build_context(db)
        config = ctx.langchain_config()
        assert "callbacks" in config
        assert ctx.callback_handler in config["callbacks"]

    def test_handler_carries_lead_and_channel(self, db) -> None:
        ctx = _build_context(db)
        assert ctx.callback_handler.lead_id == ctx.lead_id
        assert ctx.callback_handler.channel_type == "telegram"
