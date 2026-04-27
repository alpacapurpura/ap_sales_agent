"""Token-extraction fallback tests for ObservabilityCallbackHandler.

Conv 0d64c4a9 (2026-04-27) showed every Kimi K2.6 call landing in
``copilot_llm_call`` with ``input_tokens=output_tokens=0``. The handler
relied solely on the LangChain-native ``message.usage_metadata`` field,
which langchain-openai populates for upstream OpenAI but not always for
OpenAI-compatible providers (Moonshot/Kimi, DeepSeek and Qwen via custom
``base_url``). The provider does return a real ``usage`` block — it just
arrives in ``response_metadata['token_usage']`` or, with older LangChain
adapters, on the ``LLMResult.llm_output['token_usage']`` slot.

The handler must drain all three sources before reporting zeros, otherwise
trazas keep lying about cost — the user-reported failure mode that
prompted this fix.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult
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


def _pricing_snapshot():
    snap = MagicMock()
    snap.id = uuid4()
    snap.provider = "kimi"
    snap.model = "kimi-k2.6"
    snap.input_cost_per_token = Decimal("0.0000006")
    snap.output_cost_per_token = Decimal("0.0000025")
    snap.cache_read_cost_per_token = Decimal(0)
    snap.cache_write_cost_per_token = Decimal(0)
    snap.valid_from = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
    snap.valid_to = None
    return snap


def _make_handler(db):
    from src.modules.copilot.observability.persistence.llm_call_repository import LlmCallRepository
    from src.modules.copilot.observability.persistence.trace_event_repository import (
        TraceEventRepository,
    )
    from src.modules.copilot.observability.pricing.resolver import PricingResult
    from src.modules.copilot.observability.recording.callback_handler import (
        ObservabilityCallbackHandler,
    )

    pricing_resolver = MagicMock()
    pricing_resolver.resolve.return_value = PricingResult(
        snapshot=_pricing_snapshot(),
        is_estimated=False,
    )
    fx_resolver = MagicMock()
    fx_resolver.resolve.return_value = (Decimal(1), "passthrough")

    return ObservabilityCallbackHandler(
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        user_id=uuid4(),
        turn_id=uuid4(),
        llm_call_repo=LlmCallRepository(db),
        trace_repo=TraceEventRepository(db),
        pricing_resolver=pricing_resolver,
        fx_resolver=fx_resolver,
        tenant_currency="USD",
        role="agent",
    )


def _drive_turn(handler, *, response: LLMResult) -> None:
    """Open + close a synthetic Kimi span and let the handler write rows."""
    run_id = uuid4()
    handler.on_chat_model_start(
        serialized={"id": ["langchain", "chat_models", "openai", "ChatOpenAI"]},
        messages=[[]],
        run_id=run_id,
        metadata={"ls_provider": "kimi", "ls_model_name": "kimi-k2.6"},
    )
    handler.on_llm_end(response, run_id=run_id)


def _ai_message_no_usage(*, response_metadata: dict | None = None) -> AIMessage:
    """Build an AIMessage with ``usage_metadata=None`` even when
    ``response_metadata.token_usage`` is set.

    LangChain's ``AIMessage`` runs a model validator that auto-syncs an
    OpenAI-shape ``token_usage`` block in ``response_metadata`` into
    ``usage_metadata`` — masking the very fallback we need to verify.
    Building via ``model_construct`` skips validators so the test exercises
    the handler's own extraction path, not LangChain's auto-sync.
    """
    return AIMessage.model_construct(
        content="ok",
        response_metadata=response_metadata or {},
        usage_metadata=None,
    )


class TestUsageFallbacksFromResponseMetadata:
    """When ``usage_metadata`` is missing the handler reads ``response_metadata.token_usage``."""

    def test_response_metadata_token_usage_is_used(self, db) -> None:
        from src.modules.copilot.observability.persistence.models.llm_call_model import (
            CopilotLlmCallModel,
        )

        handler = _make_handler(db)
        # OpenAI-compat providers (Moonshot, DeepSeek) typically populate
        # ``response_metadata.token_usage`` with the raw OpenAI ``usage``
        # block. ``usage_metadata`` is left untouched in those clients.
        msg = _ai_message_no_usage(
            response_metadata={
                "model_name": "kimi-k2.6",
                "token_usage": {
                    "prompt_tokens": 4277,
                    "completion_tokens": 239,
                    "total_tokens": 4516,
                    "prompt_tokens_details": {"cached_tokens": 0},
                },
            },
        )
        _drive_turn(
            handler,
            response=LLMResult(generations=[[ChatGeneration(message=msg)]], llm_output=None),
        )
        db.flush()

        rows = db.query(CopilotLlmCallModel).filter_by(tenant_id=handler.tenant_id).all()
        assert len(rows) == 1
        assert rows[0].input_tokens == 4277
        assert rows[0].output_tokens == 239
        # Pricing matches ``_pricing_snapshot``: 4277 * 6e-7 + 239 * 25e-7
        # = 0.00256620 + 0.00059750 = 0.00316370.
        assert rows[0].cost_usd == Decimal("0.0031637000")

    def test_cached_tokens_from_response_metadata_propagate(self, db) -> None:
        from src.modules.copilot.observability.persistence.models.llm_call_model import (
            CopilotLlmCallModel,
        )

        handler = _make_handler(db)
        msg = _ai_message_no_usage(
            response_metadata={
                "model_name": "kimi-k2.6",
                "token_usage": {
                    "prompt_tokens": 1000,
                    "completion_tokens": 100,
                    "prompt_tokens_details": {"cached_tokens": 750},
                },
            },
        )
        _drive_turn(
            handler,
            response=LLMResult(generations=[[ChatGeneration(message=msg)]]),
        )
        db.flush()

        row = db.query(CopilotLlmCallModel).filter_by(tenant_id=handler.tenant_id).one()
        assert row.input_tokens == 1000
        assert row.cached_read_tokens == 750


class TestUsageFallbackFromLLMOutput:
    """``LLMResult.llm_output['token_usage']`` is the last-resort source."""

    def test_llm_output_token_usage_is_used_when_message_is_silent(self, db) -> None:
        from src.modules.copilot.observability.persistence.models.llm_call_model import (
            CopilotLlmCallModel,
        )

        handler = _make_handler(db)
        # Some OpenAI-compat clients (older langchain-openai versions and a
        # handful of self-hosted gateways) only populate the aggregate at
        # the LLMResult level. Both the message's ``usage_metadata`` and
        # ``response_metadata`` come back empty.
        msg = _ai_message_no_usage(response_metadata={"model_name": "kimi-k2.6"})
        _drive_turn(
            handler,
            response=LLMResult(
                generations=[[ChatGeneration(message=msg)]],
                llm_output={
                    "token_usage": {
                        "prompt_tokens": 800,
                        "completion_tokens": 200,
                    },
                },
            ),
        )
        db.flush()

        row = db.query(CopilotLlmCallModel).filter_by(tenant_id=handler.tenant_id).one()
        assert row.input_tokens == 800
        assert row.output_tokens == 200


class TestZeroTokensRemainsLastResort:
    """When every source is empty the handler still records the call honestly."""

    def test_no_usage_anywhere_records_zero_without_crashing(self, db) -> None:
        from src.modules.copilot.observability.persistence.models.llm_call_model import (
            CopilotLlmCallModel,
        )

        handler = _make_handler(db)
        msg = _ai_message_no_usage(response_metadata={"model_name": "kimi-k2.6"})
        _drive_turn(
            handler,
            response=LLMResult(generations=[[ChatGeneration(message=msg)]], llm_output=None),
        )
        db.flush()

        row = db.query(CopilotLlmCallModel).filter_by(tenant_id=handler.tenant_id).one()
        assert row.input_tokens == 0
        assert row.output_tokens == 0
        assert row.status == "ok"
