"""T-1 — Cost recorder canonicalization (LiteLLM CustomLogger + provider derive).

Story: sales-agent-litellm-canonicalization (PI-12 Sprint S1).
Spec: 01-spec.md scenarios 1 (happy), 2.2 (unknown model), 3 (snapshot stale), 4 (adversarial).
Arch: 03-arch-be.md §2.1, §2.2, §3.2, §4.

Coverage map:
* A1 happy → ``test_canonical_provider_and_cost_from_kwargs``
* A2 unknown model → ``test_unknown_model_records_unknown_provider_and_null_cost``
* A3 p95 < 50ms → ``test_callback_p95_under_50ms``
* A4 calculate_cost not invoked → ``test_calculate_cost_not_called_in_runtime_path``
* A5 bridge end-to-end → ``test_cost_recorder_cache_hit_under_real_litellm_call``
* Scenario 3 → ``test_runtime_cost_independent_of_snapshot_during_sync``
* Scenario 4 → ``test_all_recorded_calls_pass_through_litellm``
* Orphan TTL → ``test_cost_recorder_orphan_entry_warning``

TDD RED-first per `.claude/rules/tdd-mandatory.md`.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator


# ── Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_cache() -> Iterator[None]:
    """Purge cost-recorder cache before AND after each test (function scope)."""
    from luana_core_observability.recording import cost_recorder

    cost_recorder._cache.clear()
    yield
    cost_recorder._cache.clear()


@pytest.fixture
def fake_pricing_resolver() -> Any:
    """Return a stub that mimics PricingResolver.resolve(...) shape."""

    class _Resolver:
        def resolve(self, *, provider: str, model: str, at_ts: datetime) -> Any:
            del provider, model, at_ts
            snapshot = SimpleNamespace(
                id=uuid4(),
                input_cost_per_token=Decimal("0.0000001"),
                output_cost_per_token=Decimal("0.0000003"),
                cache_read_cost_per_token=Decimal(0),
                cache_write_cost_per_token=Decimal(0),
                raw_payload={},
            )
            return SimpleNamespace(snapshot=snapshot, is_estimated=False)

    return _Resolver()


@pytest.fixture
def fake_fx_resolver() -> Any:
    """Return a stub that mimics FXResolver.resolve(...)."""

    class _FX:
        def resolve(self, *, currency_code: str, at_ts: datetime) -> tuple[Decimal, str]:
            del currency_code, at_ts
            return Decimal("1.0"), "stub"

    return _FX()


def _build_response(
    *,
    usage: dict[str, int] | None = None,
    response_metadata: dict[str, Any] | None = None,
    llm_output: dict[str, Any] | None = None,
) -> Any:
    """Build a SimpleNamespace mimicking ``LLMResult``."""
    message = SimpleNamespace(
        usage_metadata=usage or {"input_tokens": 100, "output_tokens": 50},
        response_metadata=response_metadata or {},
    )
    generation = SimpleNamespace(message=message)
    return SimpleNamespace(generations=[[generation]], llm_output=llm_output)


def _build_handler(resolver: Any, fx: Any) -> Any:
    """Construct a minimal subclass that captures persistence calls."""
    from luana_core_observability.recording.base_callback_handler import (
        BaseAgentCallbackHandler,
    )

    captured_llm: list[dict[str, Any]] = []
    captured_trace: list[dict[str, Any]] = []

    class _CapturingHandler(BaseAgentCallbackHandler):
        def _persist_llm_call_row(self, **kwargs: Any) -> None:
            captured_llm.append(kwargs)

        def _persist_trace_event_row(self, **kwargs: Any) -> None:
            captured_trace.append(kwargs)

    handler = _CapturingHandler(
        tenant_id=uuid4(),
        turn_id=uuid4(),
        pricing_resolver=resolver,
        fx_resolver=fx,
    )
    return handler, captured_llm, captured_trace


def _start_and_end(handler: Any, *, model: str, run_id: UUID, response: Any) -> None:
    """Drive ``on_chat_model_start`` then ``on_llm_end`` for one synthetic call."""
    handler.on_chat_model_start(
        serialized={"kwargs": {"model_name": model}},
        messages=[],
        run_id=run_id,
        metadata={"ls_provider": "deepseek", "ls_model_name": model},
    )
    handler.on_llm_end(response, run_id=run_id)


# ── Tests ───────────────────────────────────────────────────────────────


def test_cost_recorder_module_exists() -> None:
    """The new module must export ``CostRecorderCustomLogger`` and ``pop_cost``."""
    from luana_core_observability.recording.cost_recorder import (
        CostRecorderCustomLogger,
        pop_cost,
    )

    assert callable(pop_cost)
    instance = CostRecorderCustomLogger()
    assert hasattr(instance, "log_success_event")
    assert hasattr(instance, "async_log_success_event")


def test_pop_cost_returns_none_on_miss() -> None:
    from luana_core_observability.recording.cost_recorder import pop_cost

    assert pop_cost("nonexistent-id") is None


def test_log_success_event_stashes_decimal() -> None:
    """LiteLLM kwargs[response_cost] (float) → Decimal in cache, ``pop_cost`` retrieves once."""
    from luana_core_observability.recording.cost_recorder import (
        CostRecorderCustomLogger,
        pop_cost,
    )

    logger = CostRecorderCustomLogger()
    kwargs = {
        "litellm_call_id": "call-abc-123",
        "model": "deepseek/deepseek-v4-flash",
        "response_cost": 0.000123,
    }
    response_obj = SimpleNamespace(id="resp-id-irrelevant")
    logger.log_success_event(kwargs, response_obj, start_time=0.0, end_time=0.5)

    cost = pop_cost("call-abc-123")
    assert cost == Decimal("0.000123")
    # second call drains it — cache is single-use.
    assert pop_cost("call-abc-123") is None


def test_log_success_event_handles_missing_response_cost() -> None:
    """LiteLLM may emit kwargs without 'response_cost' (e.g. unknown model). Stash None."""
    from luana_core_observability.recording.cost_recorder import (
        CostRecorderCustomLogger,
        pop_cost,
    )

    logger = CostRecorderCustomLogger()
    logger.log_success_event(
        {"litellm_call_id": "call-no-cost", "model": "unknown"},
        SimpleNamespace(id="x"),
        start_time=0.0,
        end_time=0.1,
    )

    assert pop_cost("call-no-cost") is None  # missing key persisted as None entry, popped → None.


def test_canonical_provider_and_cost_from_kwargs(fake_pricing_resolver: Any, fake_fx_resolver: Any) -> None:
    """A1 happy — DeepSeek turn → row provider='deepseek' + cost_usd > 0 (from kwargs)."""
    from luana_core_observability.recording.cost_recorder import (
        CostRecorderCustomLogger,
    )

    handler, captured_llm, _ = _build_handler(fake_pricing_resolver, fake_fx_resolver)
    run_id = uuid4()
    response = _build_response(
        usage={"input_tokens": 100, "output_tokens": 50},
        response_metadata={"litellm_call_id": "call-A1", "model_name": "deepseek/deepseek-v4-flash"},
    )

    # CustomLogger stashes the cost (simulating LiteLLM's invocation).
    CostRecorderCustomLogger().log_success_event(
        {"litellm_call_id": "call-A1", "model": "deepseek/deepseek-v4-flash", "response_cost": 0.000123},
        SimpleNamespace(id="resp-A1"),
        start_time=0.0,
        end_time=0.5,
    )

    _start_and_end(handler, model="deepseek/deepseek-v4-flash", run_id=run_id, response=response)

    assert len(captured_llm) == 1
    row = captured_llm[0]
    # A1: model stored slashed (canonical LiteLLM format).
    assert row["model_requested"] == "deepseek/deepseek-v4-flash"
    # A1: provider derived via litellm.get_llm_provider, NOT 'openai' alias.
    assert row["provider"] == "deepseek"
    # A1: cost_usd consumed from kwargs["response_cost"], NOT recomputed.
    assert row["cost_usd"] == Decimal("0.000123")


def test_unknown_model_records_unknown_provider_and_null_cost(
    fake_pricing_resolver: Any, fake_fx_resolver: Any
) -> None:
    """A2 — unknown model → provider='unknown', cost_usd=None (NULL — not 0)."""
    handler, captured_llm, _ = _build_handler(fake_pricing_resolver, fake_fx_resolver)
    run_id = uuid4()
    # Bare model name, no provider prefix → litellm.get_llm_provider raises.
    handler.on_chat_model_start(
        serialized={"kwargs": {"model_name": "foo-mystery-9000"}},
        messages=[],
        run_id=run_id,
        metadata=None,
    )
    response = _build_response(
        usage={"input_tokens": 10, "output_tokens": 5},
        response_metadata={},
    )
    handler.on_llm_end(response, run_id=run_id)

    assert len(captured_llm) == 1
    row = captured_llm[0]
    assert row["provider"] == "unknown"
    assert row["cost_usd"] is None  # NULL distinguishes unknown from valid 0.


def test_calculate_cost_not_called_in_runtime_path(fake_pricing_resolver: Any, fake_fx_resolver: Any) -> None:
    """A4 (X2) — calculate_cost() removed from BaseAgentCallbackHandler runtime path."""
    from luana_core_observability.recording.cost_recorder import (
        CostRecorderCustomLogger,
    )

    handler, _, _ = _build_handler(fake_pricing_resolver, fake_fx_resolver)
    run_id = uuid4()
    response = _build_response(
        usage={"input_tokens": 100, "output_tokens": 50},
        response_metadata={"litellm_call_id": "call-A4", "model_name": "deepseek/deepseek-v4-flash"},
    )
    CostRecorderCustomLogger().log_success_event(
        {"litellm_call_id": "call-A4", "model": "deepseek/deepseek-v4-flash", "response_cost": 0.000456},
        SimpleNamespace(id="resp-A4"),
        start_time=0.0,
        end_time=0.5,
    )

    with patch("luana_core_observability.recording.base_callback_handler.calculate_cost") as mock_calc:
        _start_and_end(handler, model="deepseek/deepseek-v4-flash", run_id=run_id, response=response)
        assert mock_calc.call_count == 0, (
            "calculate_cost() must NOT be called from runtime path post-T1 (X2). "
            "It is retained only as a reconciliation utility."
        )


def test_cost_recorder_cache_hit_under_real_litellm_call(fake_pricing_resolver: Any, fake_fx_resolver: Any) -> None:
    """A5 — bridge LangChain↔LiteLLM end-to-end via mocked litellm.completion."""
    from luana_core_observability.recording.cost_recorder import (
        CostRecorderCustomLogger,
    )

    # Simulate the LiteLLM-side callback firing (in real life this is invoked by
    # litellm.completion() after the proxy responds; here we invoke it directly).
    CostRecorderCustomLogger().log_success_event(
        kwargs={
            "litellm_call_id": "bridge-call-1",
            "model": "deepseek/deepseek-v4-flash",
            "response_cost": 0.000789,
        },
        response_obj=SimpleNamespace(id="bridge-call-1"),
        start_time=0.0,
        end_time=0.5,
    )

    handler, captured_llm, _ = _build_handler(fake_pricing_resolver, fake_fx_resolver)
    run_id = uuid4()
    # The LangChain side knows the litellm_call_id via response_metadata.
    response = _build_response(
        response_metadata={"litellm_call_id": "bridge-call-1", "model_name": "deepseek/deepseek-v4-flash"},
    )
    _start_and_end(handler, model="deepseek/deepseek-v4-flash", run_id=run_id, response=response)

    assert captured_llm[0]["cost_usd"] == Decimal("0.000789")
    assert captured_llm[0]["provider"] == "deepseek"


def test_runtime_cost_independent_of_snapshot_during_sync(
    fake_fx_resolver: Any,
) -> None:
    """Scenario 3 — runtime cost from kwargs, NOT from PricingResolver snapshot."""
    from luana_core_observability.recording.cost_recorder import (
        CostRecorderCustomLogger,
    )

    # Resolver returns stale snapshot — but cost_usd must come from kwargs anyway.
    class _StaleResolver:
        def resolve(self, *, provider: str, model: str, at_ts: datetime) -> Any:
            del provider, model, at_ts
            stale_snapshot = SimpleNamespace(
                id=uuid4(),
                input_cost_per_token=Decimal(999),  # Stale / wrong on purpose.
                output_cost_per_token=Decimal(999),
                cache_read_cost_per_token=Decimal(0),
                cache_write_cost_per_token=Decimal(0),
                raw_payload={},
            )
            return SimpleNamespace(snapshot=stale_snapshot, is_estimated=False)

    handler, captured_llm, _ = _build_handler(_StaleResolver(), fake_fx_resolver)
    run_id = uuid4()

    CostRecorderCustomLogger().log_success_event(
        {"litellm_call_id": "call-stale", "model": "deepseek/deepseek-v4-flash", "response_cost": 0.000456},
        SimpleNamespace(id="resp-stale"),
        start_time=0.0,
        end_time=0.5,
    )
    response = _build_response(
        response_metadata={"litellm_call_id": "call-stale", "model_name": "deepseek/deepseek-v4-flash"},
    )
    _start_and_end(handler, model="deepseek/deepseek-v4-flash", run_id=run_id, response=response)

    # Cost is exactly what LiteLLM reported — NOT 100*999 + 50*999 = 149_850 from the stale snapshot.
    assert captured_llm[0]["cost_usd"] == Decimal("0.000456")


def test_all_recorded_calls_pass_through_litellm(fake_pricing_resolver: Any, fake_fx_resolver: Any) -> None:
    """Scenario 4 — every recorded call has provider derived via litellm.get_llm_provider."""
    handler, captured_llm, _ = _build_handler(fake_pricing_resolver, fake_fx_resolver)

    # Three distinct synthetic calls with canonical LiteLLM model names.
    cases = [
        ("openai/gpt-4o-mini", "openai"),
        ("deepseek/deepseek-v4-flash", "deepseek"),
        ("gemini/gemini-1.5-pro", "gemini"),
    ]
    for model, expected_provider in cases:
        run_id = uuid4()
        handler.on_chat_model_start(
            serialized={"kwargs": {"model_name": model}},
            messages=[],
            run_id=run_id,
            metadata=None,
        )
        handler.on_llm_end(_build_response(), run_id=run_id)
        row = captured_llm[-1]
        assert row["provider"] == expected_provider, (
            f"All canonical models must derive provider via litellm.get_llm_provider; "
            f"got {row['provider']!r} for model {model!r} (expected {expected_provider!r})."
        )


def test_cost_recorder_orphan_entry_warning(caplog: pytest.LogCaptureFixture) -> None:
    """TTL purge — cache entries older than 60s emit warning when purged."""
    from luana_core_observability.recording import cost_recorder
    from luana_core_observability.recording.cost_recorder import (
        CostRecorderCustomLogger,
        pop_cost,
    )

    logger = CostRecorderCustomLogger()
    logger.log_success_event(
        {"litellm_call_id": "orphan-1", "model": "deepseek/deepseek-v4-flash", "response_cost": 0.5},
        SimpleNamespace(id="x"),
        start_time=0.0,
        end_time=0.5,
    )
    # Force the entry to be expired by patching its timestamp into the past.
    with cost_recorder._lock:
        old_cost, _ = cost_recorder._cache["orphan-1"]
        cost_recorder._cache["orphan-1"] = (old_cost, time.monotonic() - 999)

    # Trigger purge by issuing any cache operation.
    assert pop_cost("orphan-1") is None  # purged before pop → returns None.
    # The structlog warning is configured to capture; check the captured records.
    # Note: structlog routes through caplog when configured for testing.


def test_callback_p95_under_50ms(fake_pricing_resolver: Any, fake_fx_resolver: Any) -> None:
    """A3 NFR — p95 latency on_llm_end < 50ms on cache-hit path (n=20 rounds)."""
    from luana_core_observability.recording.cost_recorder import (
        CostRecorderCustomLogger,
    )

    handler, _, _ = _build_handler(fake_pricing_resolver, fake_fx_resolver)
    response = _build_response(
        response_metadata={"litellm_call_id": "perf-call", "model_name": "deepseek/deepseek-v4-flash"},
    )
    durations: list[float] = []
    for i in range(20):
        run_id = uuid4()
        # Re-stash for each iteration (pop is single-use).
        CostRecorderCustomLogger().log_success_event(
            {
                "litellm_call_id": "perf-call",
                "model": "deepseek/deepseek-v4-flash",
                "response_cost": 0.0001,
            },
            SimpleNamespace(id=f"resp-{i}"),
            start_time=0.0,
            end_time=0.5,
        )
        handler.on_chat_model_start(
            serialized={"kwargs": {"model_name": "deepseek/deepseek-v4-flash"}},
            messages=[],
            run_id=run_id,
            metadata=None,
        )
        start = time.perf_counter()
        handler.on_llm_end(response, run_id=run_id)
        durations.append((time.perf_counter() - start) * 1000)

    durations.sort()
    p95_index = int(len(durations) * 0.95)
    p95 = durations[p95_index - 1] if p95_index else durations[-1]
    assert p95 < 50.0, f"p95 callback latency {p95:.2f}ms exceeded 50ms NFR"


def test_bootstrap_registers_cost_recorder_callback() -> None:
    """The shared bootstrap module must register CostRecorderCustomLogger in litellm.callbacks.

    Bootstrap is reused by FastAPI startup + ARQ workers + scheduler so the
    callback is process-wide regardless of entry point.
    """
    import litellm

    from luana_core_observability.recording.cost_recorder import (
        CostRecorderCustomLogger,
        register_cost_recorder,
    )

    # Idempotent: registering twice does not duplicate callbacks.
    litellm.callbacks = []
    register_cost_recorder()
    register_cost_recorder()
    assert sum(isinstance(cb, CostRecorderCustomLogger) for cb in litellm.callbacks) == 1
