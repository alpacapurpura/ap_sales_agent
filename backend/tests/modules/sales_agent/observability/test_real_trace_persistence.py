"""Real DB persistence — Bug #2 regression guard (PR-2 PI-1.1).

NO mocks of the SQLAlchemy session. Constructs a real
:class:`SalesAgentObservabilityContext` against an in-memory SQLite
session bound to the same model registry the production code uses,
runs ``observe_turn`` end-to-end, and asserts the rows landed in
``sales_agent_trace_event`` (columnar — not JSONB sniff).

Bug #2 root cause (pre-PR-2): the orchestrator wired only the
``SalesAgentCallbackHandler`` via ``RunnableConfig(callbacks=[...])``.
The handler captures LLM/tool events; turn brackets (``turn_start`` /
``turn_end``) were never emitted because no envelope wrapped the
``ainvoke``. Result: zero rows for sales_agent across thousands of
turns.

This test reproduces the desired post-fix behavior:

1. ``observe_turn`` enter writes ``turn_start`` row.
2. ``observe_turn`` clean exit writes ``turn_end`` row.
3. Both rows carry ``tenant_id`` + ``lead_id`` + ``channel_type``
   (sales-agent-specific columns).
4. Status ``ok`` on clean exit.

Marker ``verify`` — included in ``/test-all`` per ``conftest.py`` markers.
Excluded from default fast suite to keep iteration loop tight.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def real_db(db_engine):
    """Real-ish session bound to the in-memory SQLite test engine.

    "Real" in the sense that no part of the SalesAgentObservabilityContext
    flow is mocked — repos, tables, INSERT path are all genuine SQLA
    operations against the test schema. Postgres-specific JSONB / UUID
    are mapped to text/CHAR(36) via the conftest ``MockJSONB`` /
    ``MockUUID`` shims so SQLite can host the same model definitions.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _make_context(real_db, *, lead_id=None, channel_type="telegram"):
    from luana_core_sales_agent.observability.persistence.llm_call_repository import (
        SalesAgentLlmCallRepository,
    )
    from luana_core_sales_agent.observability.persistence.trace_event_repository import (
        SalesAgentTraceEventRepository,
    )
    from luana_core_sales_agent.observability.recording.turn_envelope import (
        SalesAgentObservabilityContext,
    )

    pricing_resolver = MagicMock()
    fx_resolver = MagicMock()
    fx_resolver.resolve.return_value = (Decimal(1), "passthrough")

    return SalesAgentObservabilityContext.start(
        tenant_id=uuid4(),
        lead_id=lead_id or uuid4(),
        channel_type=channel_type,
        llm_call_repo=SalesAgentLlmCallRepository(real_db),
        trace_repo=SalesAgentTraceEventRepository(real_db),
        pricing_resolver=pricing_resolver,
        fx_resolver=fx_resolver,
        db_session=real_db,
        tenant_currency="USD",
        role="agent",
    )


@pytest.mark.verify
class TestRealTracePersistence:
    """Real persistence — no DB session mocks. Bug #2 regression guard."""

    @pytest.mark.asyncio
    async def test_observe_turn_inserts_turn_start_and_turn_end(self, real_db) -> None:
        """Pre-PR-2 this asserted ZERO rows. Post-PR-2 it asserts >=2."""
        from luana_core_sales_agent.observability.persistence.models.trace_event_model import (
            SalesAgentTraceEventModel,
        )

        ctx = _make_context(real_db, channel_type="telegram")

        async with ctx.observe_turn(message="hola", route="sales_agent", attachments=[]):
            # No graph call — just exercise the bracket lifecycle.
            pass

        real_db.flush()
        rows = (
            real_db.query(SalesAgentTraceEventModel)
            .filter_by(turn_id=ctx.turn_id)
            .order_by(SalesAgentTraceEventModel.created_at.asc())
            .all()
        )
        # Bug #2 assertion: >= 2 rows MUST land. Pre-PR-2 = 0.
        assert len(rows) >= 2, (
            f"Bug #2 regression: expected >=2 trace_event rows for turn "
            f"{ctx.turn_id}, got {len(rows)}. Envelope ``observe_turn`` did "
            f"not write turn_start/turn_end."
        )
        events = {r.event_type for r in rows}
        assert "turn_start" in events
        assert "turn_end" in events
        # Sales-agent-specific columns populated:
        for r in rows:
            assert r.tenant_id == ctx.tenant_id
            assert r.lead_id == ctx.lead_id
            assert r.channel_type == "telegram"

    @pytest.mark.asyncio
    async def test_observe_turn_marks_status_ok_on_clean_exit(self, real_db) -> None:
        from luana_core_sales_agent.observability.persistence.models.trace_event_model import (
            SalesAgentTraceEventModel,
        )

        ctx = _make_context(real_db)
        async with ctx.observe_turn(message="hola", route="sales_agent", attachments=[]):
            pass
        real_db.flush()

        end_row = real_db.query(SalesAgentTraceEventModel).filter_by(turn_id=ctx.turn_id, event_type="turn_end").one()
        assert end_row.status == "ok"

    @pytest.mark.asyncio
    async def test_observe_turn_with_in_band_llm_call_persists_three_rows(
        self,
        real_db,
    ) -> None:
        """Real DB: simulate one ``llm_call`` row landing during the turn.

        End state: 3 rows in ``sales_agent_trace_event`` is overcounting —
        the callback handler writes ``llm_call`` to trace_event mirror +
        a row to ``sales_agent_llm_call``. Here we simulate just the
        columnar ``sales_agent_llm_call`` insert (skip the handler) and
        verify the envelope still emits its 2 brackets + the aggregator
        sees the row.
        """
        import datetime as dt

        from luana_core_sales_agent.observability.persistence.models.llm_call_model import (
            SalesAgentLlmCallModel,
        )
        from luana_core_sales_agent.observability.persistence.models.trace_event_model import (
            SalesAgentTraceEventModel,
        )

        ctx = _make_context(real_db)

        async with ctx.observe_turn(message="hola", route="sales_agent", attachments=[]):
            real_db.add(
                SalesAgentLlmCallModel(
                    tenant_id=ctx.tenant_id,
                    lead_id=ctx.lead_id,
                    channel_type=ctx.channel_type,
                    turn_id=ctx.turn_id,
                    span_id=uuid4(),
                    role="agent",
                    provider="moonshot",
                    model_requested="kimi-k2.6",
                    model_responded="kimi-k2.6",
                    input_tokens=1000,
                    output_tokens=500,
                    cached_read_tokens=0,
                    cached_write_tokens=0,
                    reasoning_tokens=0,
                    pricing_version_id=uuid4(),
                    input_unit_cost_usd=Decimal("0.0000004"),
                    output_unit_cost_usd=Decimal("0.000002"),
                    cached_read_unit_cost_usd=Decimal(0),
                    cost_usd=Decimal("0.0014"),
                    tenant_currency="USD",
                    fx_rate_to_tenant=Decimal(1),
                    fx_rate_source="passthrough",
                    cost_tenant_currency=Decimal("0.0014"),
                    started_at=dt.datetime.now(tz=dt.UTC),
                    duration_ms=500,
                    status="ok",
                ),
            )
            real_db.flush()
        real_db.flush()

        bracket_rows = real_db.query(SalesAgentTraceEventModel).filter_by(turn_id=ctx.turn_id).all()
        assert len(bracket_rows) >= 2  # turn_start + turn_end

        end_row = next(r for r in bracket_rows if r.event_type == "turn_end")
        # Aggregator picked up the in-band llm_call row.
        assert (end_row.data or {}).get("llm_call_count") == 1
        assert (end_row.data or {}).get("total_input_tokens") == 1000
        assert (end_row.data or {}).get("total_output_tokens") == 500
