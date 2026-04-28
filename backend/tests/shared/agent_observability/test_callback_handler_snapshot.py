"""Snapshot test — pre/post-lift safety net for S11A.

Replays a deterministic sequence of LangChain callbacks against both
agent handlers (sales_agent + copilot) and asserts the captured rows
match a JSON baseline byte-equal.

If S11A's :class:`BaseAgentCallbackHandler` lift preserves behavior, the
diff is zero. Any divergence (extra row, reordered call, changed kwarg
shape) fails the test and surfaces the offending payload — that's the
contract.

The snapshot intentionally excludes the actual LLM response text and
real timing — those are already covered by the handler's own unit
tests. Snapshots track *shape*, not content.

# [SALES-AGENT-CALLBACK-SNAPSHOT-S11A] -> docs/domains/sales-agent/redesign-2026-04/phases/S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.shared.agent_observability._callback_snapshot_helpers import (
    CONVERSATION_ID,
    LEAD_ID,
    TENANT_ID,
    TURN_ID,
    USER_ID,
    assert_matches_snapshot,
    build_capturing_repos,
    build_fx_resolver_stub,
    build_pricing_resolver_stub,
    freeze_handler_clock,
    render_snapshot,
    replay_canonical_sequence,
)

if TYPE_CHECKING:
    import pytest

# ── Sales agent handler ─────────────────────────────────────────────────


def test_sales_agent_callback_handler_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sales handler emits the canonical row sequence for the canonical events."""
    freeze_handler_clock(
        monkeypatch,
        "src.modules.sales_agent.observability.recording.callback_handler",
    )

    from src.modules.sales_agent.observability.recording.callback_handler import (
        SalesAgentCallbackHandler,
    )

    llm_repo, trace_repo = build_capturing_repos()
    db_session_stub = type("Sess", (), {"rollback": staticmethod(lambda: None)})()

    handler = SalesAgentCallbackHandler(
        tenant_id=TENANT_ID,
        lead_id=LEAD_ID,
        channel_type="whatsapp",
        turn_id=TURN_ID,
        llm_call_repo=llm_repo,
        trace_repo=trace_repo,
        pricing_resolver=build_pricing_resolver_stub(),
        fx_resolver=build_fx_resolver_stub(),
        db_session=db_session_stub,
        tenant_currency="USD",
        role="closer",
    )

    # span_id is a fresh uuid4 — replace with deterministic placeholder when
    # capturing so byte-equal comparison works.
    monkeypatch.setattr(
        "src.modules.sales_agent.observability.recording.callback_handler.uuid4",
        _deterministic_span_id_factory(),
    )

    replay_canonical_sequence(handler)

    snapshot = render_snapshot(llm_repo.captured, trace_repo.captured)
    assert_matches_snapshot(snapshot, "sales_handler_baseline.json")


# ── Copilot handler ────────────────────────────────────────────────────


def test_copilot_callback_handler_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    """Copilot handler emits the canonical row sequence for the canonical events."""
    freeze_handler_clock(
        monkeypatch,
        "src.modules.copilot.observability.recording.callback_handler",
    )

    from src.modules.copilot.observability.recording.callback_handler import (
        ObservabilityCallbackHandler,
    )

    llm_repo, trace_repo = build_capturing_repos()

    handler = ObservabilityCallbackHandler(
        tenant_id=TENANT_ID,
        conversation_id=CONVERSATION_ID,
        user_id=USER_ID,
        turn_id=TURN_ID,
        llm_call_repo=llm_repo,
        trace_repo=trace_repo,
        pricing_resolver=build_pricing_resolver_stub(),
        fx_resolver=build_fx_resolver_stub(),
        tenant_currency="USD",
        role="agent",
    )

    monkeypatch.setattr(
        "src.modules.copilot.observability.recording.callback_handler.uuid4",
        _deterministic_span_id_factory(),
    )

    replay_canonical_sequence(handler)

    snapshot = render_snapshot(llm_repo.captured, trace_repo.captured)
    assert_matches_snapshot(snapshot, "copilot_handler_baseline.json")


# ── Helpers ─────────────────────────────────────────────────────────────


def _deterministic_span_id_factory():  # type: ignore[no-untyped-def]
    """uuid4 stub returning sequential UUIDs so the snapshot is byte-equal."""
    from uuid import UUID

    counter = {"n": 0}

    def fake_uuid4() -> UUID:
        counter["n"] += 1
        return UUID(f"99999999-9999-9999-9999-{counter['n']:012d}")

    return fake_uuid4
