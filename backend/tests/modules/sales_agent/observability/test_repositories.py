"""Smoke + invariants for sales_agent observability repos.

Exercises:

* models can be instantiated with sales-agent-specific columns
  (``lead_id``, ``channel_type``).
* repos satisfy structural Protocols
  (:class:`BaseLLMCallRepoProtocol`,
  :class:`BaseTraceEventRepoProtocol`).
* repo ``.add(...)`` accepts the kwarg shape the callback handler will
  produce — fail-fast guards a column-rename regression.

Caller controls commit pattern; tests use a session mock to avoid
real DB writes (already validated end-to-end by alembic clone-DB run
in S1.1).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest


@pytest.fixture
def fake_session() -> MagicMock:
    """Return a mock SA Session whose ``add`` records the row."""
    return MagicMock()


class TestLlmCallRepository:
    def test_add_persists_row_with_sales_columns(self, fake_session: MagicMock) -> None:
        from src.modules.sales_agent.observability.persistence.llm_call_repository import (
            SalesAgentLlmCallRepository,
        )

        repo = SalesAgentLlmCallRepository(fake_session)
        tenant_id = uuid4()
        lead_id = uuid4()
        turn_id = uuid4()
        span_id = uuid4()
        pricing_version_id = uuid4()
        started = datetime.now(tz=UTC)

        row = repo.add(
            tenant_id=tenant_id,
            lead_id=lead_id,
            channel_type="telegram",
            turn_id=turn_id,
            span_id=span_id,
            parent_span_id=None,
            role="closer",
            provider="kimi",
            model_requested="kimi-k2.6",
            model_responded="kimi-k2.6",
            input_tokens=1000,
            output_tokens=500,
            cached_read_tokens=0,
            cached_write_tokens=0,
            reasoning_tokens=0,
            pricing_version_id=pricing_version_id,
            input_unit_cost_usd=Decimal("0.0000004"),
            output_unit_cost_usd=Decimal("0.000002"),
            cached_read_unit_cost_usd=Decimal(0),
            cost_usd=Decimal("0.0014"),
            tenant_currency="USD",
            fx_rate_to_tenant=Decimal(1),
            fx_rate_source="frankfurter",
            cost_tenant_currency=Decimal("0.0014"),
            started_at=started,
            duration_ms=1234,
            status="ok",
            error_type=None,
        )
        # Row constructed and added to session — no commit issued.
        fake_session.add.assert_called_once_with(row)
        assert row.lead_id == lead_id
        assert row.channel_type == "telegram"
        assert row.tenant_id == tenant_id

    def test_satisfies_base_protocol(self) -> None:
        from src.modules.sales_agent.observability.persistence.llm_call_repository import (
            SalesAgentLlmCallRepository,
        )
        from src.shared.agent_observability.persistence.base_llm_call_repo import (
            BaseLLMCallRepoProtocol,
        )

        repo = SalesAgentLlmCallRepository(MagicMock())
        # Structural typing: hasattr ``add`` callable.
        assert hasattr(repo, "add")
        assert callable(repo.add)
        # Runtime check via duck typing — Protocol has runtime_checkable
        # only when decorated; we only assert the shape here.
        assert isinstance(repo, BaseLLMCallRepoProtocol)


class TestTraceEventRepository:
    def test_add_persists_row_with_sales_columns(self, fake_session: MagicMock) -> None:
        from src.modules.sales_agent.observability.persistence.trace_event_repository import (
            SalesAgentTraceEventRepository,
        )

        repo = SalesAgentTraceEventRepository(fake_session)
        tenant_id = uuid4()
        lead_id = uuid4()
        turn_id = uuid4()
        span_id = uuid4()

        row = repo.add(
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=span_id,
            event_type="turn_start",
            name="sales_turn",
            data={"channel": "telegram"},
            duration_ms=None,
            status="ok",
            lead_id=lead_id,
            channel_type="telegram",
        )
        fake_session.add.assert_called_once_with(row)
        assert row.lead_id == lead_id
        assert row.channel_type == "telegram"
        assert row.event_type == "turn_start"

    def test_satisfies_base_protocol(self) -> None:
        from src.modules.sales_agent.observability.persistence.trace_event_repository import (
            SalesAgentTraceEventRepository,
        )
        from src.shared.agent_observability.persistence.base_trace_event_repo import (
            BaseTraceEventRepoProtocol,
        )

        repo = SalesAgentTraceEventRepository(MagicMock())
        assert isinstance(repo, BaseTraceEventRepoProtocol)


class TestRoutingLogRepository:
    def test_add_persists_row(self, fake_session: MagicMock) -> None:
        from src.modules.sales_agent.observability.persistence.routing_log_repository import (
            SalesAgentRoutingLogRepository,
        )

        repo = SalesAgentRoutingLogRepository(fake_session)
        row = repo.add(
            tenant_id=uuid4(),
            lead_id=uuid4(),
            channel_type="telegram",
            turn_id=uuid4(),
            stage="closing",
            lead_score=85,
            tier_selected="REASONING",
            specialist_routed="closer",
            reason="lead score >= 80 and signals >= 2",
            confidence=Decimal("0.92"),
            user_msg_length=42,
            tools_available=3,
        )
        fake_session.add.assert_called_once_with(row)
        assert row.specialist_routed == "closer"
        assert row.stage == "closing"
