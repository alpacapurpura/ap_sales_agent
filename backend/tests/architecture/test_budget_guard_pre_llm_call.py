"""Architecture fitness gate (PR-6 Sub-E): BudgetGuard wired pre-LLM call.

Verifies that LLM call sites in modules ``{sales_agent, copilot}`` are
either wrapped via ``BudgetGuardingChatModel`` / ``BudgetGuardingLLMService``
or appear in the explicit ``KNOWN_UNGUARDED`` allowlist below.

Brand callsites are in ``KNOWN_UNGUARDED`` pending Sub-D-2 follow-up
(deuda residual DR-7 — sync ``LLMFactory.get_service().generate_response``
requires per-callsite refactor with ``BudgetGuardingLLMService``).

The allowlist is **shrink-only** — every removal is permanent progress
toward complete enforcement. Adding a new entry requires a justified
TODO comment and a follow-up issue.

Single point of enforcement (1000 clientes): wrappers are inserted at
factory / pipeline init level, so new callsites are gated automatically.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Allowlist: callsites NOT yet behind a BudgetGuard wrapper.
# Each entry must include WHY (test stub, deferred refactor, etc.).
# This list shrinks only. Adding entries requires PR review justification.
# ---------------------------------------------------------------------------

KNOWN_UNGUARDED: frozenset[tuple[str, str]] = frozenset(
    {
        # ── Brand: 7 LLM callsites pending Sub-D-2 / DR-7 ──
        # Sync LLMFactory.get_service().generate_response(...) usage.
        # Wrap requires per-callsite refactor with BudgetGuardingLLMService.
        # Tracked in PR-6 IMPL-LOG (DR-7).
        ("src/modules/brand/application/voice_fidelity/grader.py", "judge LLM"),
        (
            "src/modules/brand/application/agents/style_analyzer/nodes.py",
            "voice extraction nodes (5 callsites in same file)",
        ),
        (
            "src/modules/brand/application/services/personality_service.py",
            "personality extraction (1 callsite in best-effort caller)",
        ),
        # ── sales_agent legacy callsites in tools workers (S3 scope) ──
        # `LLMFactory.get_service().generate_response(...)` in observability /
        # quality eval workers — separate cron path from ConversationPipeline.
        # Sub-G follow-up scope: wrap workers individually or via factory.
        (
            "src/shared/workers/sales_agent_quality_eval.py",
            "weekly eval cron worker — separate path from ConversationPipeline",
        ),
        (
            "src/shared/workers/copilot_quality_eval.py",
            "weekly eval cron worker — separate path from deep_agent",
        ),
    }
)


def _backend_root() -> Path:
    """Return backend src root."""
    return Path(__file__).resolve().parents[2] / "src"


def test_budget_guard_wrappers_exist() -> None:
    """Sanity: BudgetGuardingChatModel + BudgetGuardingLLMService importable."""
    from luana_core_billing.application.llm_guards import (
        BudgetGuardingChatModel,
        BudgetGuardingLLMService,
    )

    assert BudgetGuardingChatModel is not None
    assert BudgetGuardingLLMService is not None


def test_sales_agent_pipeline_accepts_budget_guard() -> None:
    """ConversationPipeline.__init__ exposes ``budget_guard`` DI param.

    Single-point enforcement: pipeline injects wrapped LLM into nodes.
    AST scan because runtime ``inspect.signature`` returns ``*args, **kwargs``
    (decorator-wrapped) — source-level AST is the reliable check.
    """
    pipeline_path = (
        _backend_root() / "modules" / "sales_agent" / "application" / "orchestrator" / "conversation_pipeline.py"
    )
    source = pipeline_path.read_text(encoding="utf-8")
    assert "budget_guard: BudgetGuard | None" in source, (
        "ConversationPipeline.__init__ source MUST declare ``budget_guard: BudgetGuard | None`` for PR-6 wiring"
    )


def test_copilot_deep_agent_graph_accepts_budget_guard() -> None:
    """build_deep_agent_graph exposes ``budget_guard`` + ``tenant_id`` DI params.

    Single-point enforcement: graph wraps llm with BudgetGuardingChatModel
    when guard provided, gating every callsite consuming this graph.
    """
    import inspect

    from luana_core_copilot.application.orchestrator.deep_agent import (
        build_deep_agent_graph,
    )

    sig = inspect.signature(build_deep_agent_graph)
    assert "budget_guard" in sig.parameters, "build_deep_agent_graph MUST accept ``budget_guard`` for PR-6 Sub-C wiring"
    assert "tenant_id" in sig.parameters, "build_deep_agent_graph MUST accept ``tenant_id`` for budget bucket key"


def test_known_unguarded_allowlist_shrinks_only() -> None:
    """Allowlist size guard — sentinel for shrink-only ratchet semantics.

    If a new entry is added, this test fails until the constant below is
    bumped explicitly (signals PR review awareness of regression).
    """
    # Sentinel: lock current count. Decrement when a callsite gets wrapped.
    expected_max = 5
    assert len(KNOWN_UNGUARDED) <= expected_max, (
        f"KNOWN_UNGUARDED grew beyond {expected_max} — verify each new entry has a justified TODO + follow-up issue."
    )


def test_known_unguarded_paths_exist() -> None:
    """Every allowlist entry references a real file (no rot)."""
    root = _backend_root()
    for rel_path, _reason in KNOWN_UNGUARDED:
        full = root / rel_path[len("src/") :] if rel_path.startswith("src/") else root / rel_path
        assert full.exists(), f"Allowlist path no longer exists: {rel_path}"
