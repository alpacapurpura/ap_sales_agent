"""Unit tests for MAJ-EVAL state machine (T-5 TDD).

Pure unit tests — no LLM dispatch, no real DB. Mocks judge_registry.get_judge()
to return AsyncMock adapters that yield deterministic JudgeOpinion fixtures.
Marked @pytest.mark.no_eval so they run on default CI without --run-evals.

Coverage targets per T-5 acceptance:
- A1: Variance + weighted aggregate logic correct (be_lint, be_format, be_mypy_strict)
- A2: PII sanitize pre-judge call (validator pii_sanitize_pre_judge_call — arch test)
- A3: Round 2 peer-only — DQ3 (validator round_2_no_self_reasoning — arch test)
- A4: Unconverged fallback semantics (validator round_2_convergence_or_unconverged_flag)
- A5: R2 partial fallback semantics (validator r2_partial_fallback_judge_fail)

Tests:
- test_round_1_parallel_3_judges_returns_3_opinions
- test_variance_below_15_triggers_no_round_2
- test_variance_above_15_triggers_round_2 (D3 cement)
- test_round_2_uses_peer_only_prompts (T-7 integration — verify call args)
- test_round_2_convergence_below_10_returns_r2_avg
- test_round_2_unconverged_above_10_marks_unconverged_true
- test_r2_partial_one_judge_timeout_marks_partial
- test_aggregation_weights_sonnet_04_gpt4o_04_kimi_02 (D2 cement)
- test_suspicious_flag_when_score_1_with_injection_attempt
- test_cache_hit_short_circuits_judge_calls
- test_cache_miss_computes_then_persists
- test_cost_aggregation_sums_per_judge
- test_asyncio_gather_semaphore_concurrency_cap
- test_orchestration_per_rubric_per_turn (4 rubrics x N turns matrix)
- test_variance_max_minus_min_pure (NOT statistical)
- test_weighted_average_excludes_none_scores
- test_lt_2_valid_judges_unconverged_score_null
- test_pii_sanitize_called_pre_judge

# voseo-allowed: docstring cita rubric IDs canonicos en spec v2
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from tests.agentic_evals.sales_agent.grader._internal import maj_eval as me
from tests.agentic_evals.sales_agent.grader.result import (
    JudgeOpinion,
    MajEvalScore,
    RubricGradeRequest,
)

pytestmark = pytest.mark.no_eval  # Pure unit tests — no real LLM, no real DB


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures — fake transcripts, voice profiles, requests
# ──────────────────────────────────────────────────────────────────────────────


class _FakeTurn:
    """Duck-typed Story D GoldenTurnModel surrogate."""

    def __init__(
        self,
        *,
        role: str,
        turn_number: int,
        content: str,
        tool_calls: list[Any] | None = None,
    ) -> None:
        self.role = role
        self.turn_number = turn_number
        self.content = content
        self.tool_calls = tool_calls

    def model_copy(self, *, update: dict[str, Any]) -> _FakeTurn:
        new = _FakeTurn(
            role=self.role,
            turn_number=self.turn_number,
            content=update.get("content", self.content),
            tool_calls=self.tool_calls,
        )
        return new


class _FakeVoiceProfile:
    """Duck-typed Story A PersonalityProfile surrogate."""

    def __init__(self, *, system_instruction: str = "ASI HABLAS: warm; ASI NO: aloof") -> None:
        self.system_instruction = system_instruction
        self.dialect_code = "es-419"


def _make_request(
    *,
    transcript: list[_FakeTurn] | None = None,
    rubrics: list[str] | None = None,
    persona_kind: str = "happy",
    cache_policy: str = "use",
) -> RubricGradeRequest:
    """Build a RubricGradeRequest with sensible defaults."""
    if transcript is None:
        transcript = [
            _FakeTurn(role="customer", turn_number=1, content="Hola, busco coaching."),
            _FakeTurn(role="agent", turn_number=2, content="Hola! Te ayudo encantado."),
        ]
    if rubrics is None:
        rubrics = ["voice-fidelity"]
    return RubricGradeRequest(
        transcript=transcript,
        tenant_voice_profile=_FakeVoiceProfile(),
        rubrics=rubrics,  # type: ignore[arg-type]
        simulation_id=str(uuid4()),
        tenant_slug="tenant_demo",
        persona_kind=persona_kind,  # type: ignore[arg-type]
        actor_profile_id="actor_happy_001",
        cache_policy=cache_policy,  # type: ignore[arg-type]
    )


def _make_opinion(
    *,
    judge_id: str,
    score: float | None,
    weight: float,
    round_n: int = 1,
    confidence: float = 0.9,
    reasoning: str = "ok",
    cost_usd: Decimal = Decimal("0.001"),
    latency_ms: int = 100,
    tokens_input: int = 50,
    tokens_output: int = 30,
    cache_hit: bool = False,
    injection_attempt_detected: bool = False,
) -> JudgeOpinion:
    """Build a JudgeOpinion with sensible defaults."""
    model_used = {
        "sonnet": "claude-sonnet-4-6",
        "gpt4o": "gpt-4o-2024-11-20",
        "kimi": "kimi-k2.6",
    }[judge_id]
    return JudgeOpinion(
        judge_id=judge_id,  # type: ignore[arg-type]
        model_used=model_used,
        weight=weight,
        score=score,
        reasoning=reasoning,
        confidence=confidence,
        latency_ms=latency_ms,
        tokens_input=tokens_input,
        tokens_output=tokens_output,
        cost_usd=cost_usd,
        round_n=round_n,  # type: ignore[arg-type]
        cache_hit=cache_hit,
        injection_attempt_detected=injection_attempt_detected,
    )


def _build_obs_context() -> Any:
    """Stub EvalSimulatorObservabilityContext — used only as a pass-through."""
    obs = MagicMock()
    obs.eval_metadata = {"simulation_id": str(uuid4())}
    obs.langchain_config = MagicMock(return_value={"metadata": {}})
    return obs


def _build_session() -> Any:
    """Stub AsyncSession — execute returns Mock, no real DB."""
    session = MagicMock()
    session.execute = AsyncMock()
    return session


# ──────────────────────────────────────────────────────────────────────────────
# Pure helpers — variance + weighted average
# ──────────────────────────────────────────────────────────────────────────────


def test_variance_max_minus_min_pure() -> None:
    """variance(opinions) = max(scores) - min(scores) — D3 simple range, NOT statistical."""
    opinions = [
        _make_opinion(judge_id="sonnet", score=0.9, weight=0.4),
        _make_opinion(judge_id="gpt4o", score=0.7, weight=0.4),
        _make_opinion(judge_id="kimi", score=0.5, weight=0.2),
    ]
    # max=0.9, min=0.5 → variance = 0.4
    assert me._variance(opinions) == pytest.approx(0.4)


def test_variance_excludes_none_scores() -> None:
    """variance ignores opinions with score=None (judge fail)."""
    opinions = [
        _make_opinion(judge_id="sonnet", score=0.9, weight=0.4),
        _make_opinion(judge_id="gpt4o", score=None, weight=0.4),
        _make_opinion(judge_id="kimi", score=0.5, weight=0.2),
    ]
    # max=0.9, min=0.5 → 0.4 (None excluded)
    assert me._variance(opinions) == pytest.approx(0.4)


def test_variance_empty_returns_zero() -> None:
    """variance of empty (or all-None) returns 0.0 (not error)."""
    assert me._variance([]) == 0.0
    all_none = [_make_opinion(judge_id="sonnet", score=None, weight=0.4)]
    assert me._variance(all_none) == 0.0


def test_weighted_average_excludes_none_scores() -> None:
    """weighted average ignores None scores; renormalizes weights."""
    opinions = [
        _make_opinion(judge_id="sonnet", score=0.8, weight=0.4),
        _make_opinion(judge_id="gpt4o", score=None, weight=0.4),
        _make_opinion(judge_id="kimi", score=0.6, weight=0.2),
    ]
    # weights = 0.4 + 0.2 = 0.6 (gpt4o excluded), values = 0.8*0.4 + 0.6*0.2 = 0.32 + 0.12 = 0.44
    # avg = 0.44 / 0.6 ≈ 0.7333
    assert me._weighted_average(opinions) == pytest.approx(0.44 / 0.6)


def test_aggregation_weights_sonnet_04_gpt4o_04_kimi_02() -> None:
    """D2 cement: weighted avg uses 0.4/0.4/0.2 weights."""
    opinions = [
        _make_opinion(judge_id="sonnet", score=1.0, weight=0.4),
        _make_opinion(judge_id="gpt4o", score=0.5, weight=0.4),
        _make_opinion(judge_id="kimi", score=0.0, weight=0.2),
    ]
    # 1.0*0.4 + 0.5*0.4 + 0.0*0.2 = 0.4 + 0.2 + 0.0 = 0.6
    assert me._weighted_average(opinions) == pytest.approx(0.6)


def test_weighted_average_zero_weight_returns_zero() -> None:
    """If all weights ineffective (all scores None), returns 0.0 — defense."""
    opinions = [
        _make_opinion(judge_id="sonnet", score=None, weight=0.4),
        _make_opinion(judge_id="gpt4o", score=None, weight=0.4),
        _make_opinion(judge_id="kimi", score=None, weight=0.2),
    ]
    assert me._weighted_average(opinions) == 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Round 1 + Round 2 state machine — happy path scenarios
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_round_1_parallel_3_judges_returns_3_opinions() -> None:
    """Round 1: 3 judges invoked via asyncio.gather; MajEvalScore.judges has 3 entries."""
    request = _make_request()
    obs_context = _build_obs_context()

    # Mock get_judge to return adapters whose .grade returns deterministic opinions
    def _make_adapter(judge_id: str, model: str, score: float) -> Any:
        adapter = MagicMock()
        adapter.judge_id = judge_id
        adapter.model = model
        weight = me.JUDGE_WEIGHTS[judge_id]
        adapter.grade = AsyncMock(
            return_value=_make_opinion(judge_id=judge_id, score=score, weight=weight, round_n=1),
        )
        return adapter

    adapters = {
        "sonnet": _make_adapter("sonnet", "claude-sonnet-4-6", 0.85),
        "gpt4o": _make_adapter("gpt4o", "gpt-4o-2024-11-20", 0.82),
        "kimi": _make_adapter("kimi", "kimi-k2.6", 0.80),
    }

    with (
        patch.object(me, "get_judge", side_effect=lambda jid: adapters[jid]),
        patch.object(me, "build_judge_prompt", return_value=[{"role": "system", "content": "ok"}]),
        patch.object(me, "cache_lookup", AsyncMock(return_value=None)),
        patch.object(me, "cache_persist", AsyncMock(return_value=None)),
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)),
        patch.object(me, "_get_rubric_version", return_value=1),
    ):
        session = _build_session()
        results = await me.grade_transcript_maj_eval(request, session=session, obs_context=obs_context)

    assert len(results) == 2  # 2 turns x 1 rubric
    for score in results:
        assert isinstance(score, MajEvalScore)
        assert len(score.judges) == 3  # Round 1 only — variance < 0.15
        assert score.debate_triggered is False
        assert score.unconverged is False


@pytest.mark.asyncio
async def test_variance_below_15_triggers_no_round_2() -> None:
    """variance < 0.15 → debate_triggered=False; only 3 R1 opinions (no R2)."""
    request = _make_request(transcript=[_FakeTurn(role="agent", turn_number=1, content="ok")])
    obs_context = _build_obs_context()

    # Sonnet=0.85, GPT-4o=0.82, Kimi=0.80 → variance = 0.05 < 0.15
    def _adapter(jid: str, score: float) -> Any:
        a = MagicMock()
        a.grade = AsyncMock(
            return_value=_make_opinion(judge_id=jid, score=score, weight=me.JUDGE_WEIGHTS[jid]),
        )
        return a

    adapters = {"sonnet": _adapter("sonnet", 0.85), "gpt4o": _adapter("gpt4o", 0.82), "kimi": _adapter("kimi", 0.80)}

    with (
        patch.object(me, "get_judge", side_effect=lambda jid: adapters[jid]),
        patch.object(me, "build_judge_prompt", return_value=[{"role": "system", "content": "ok"}]),
        patch.object(me, "cache_lookup", AsyncMock(return_value=None)),
        patch.object(me, "cache_persist", AsyncMock(return_value=None)),
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)),
        patch.object(me, "_get_rubric_version", return_value=1),
    ):
        results = await me.grade_transcript_maj_eval(request, session=_build_session(), obs_context=obs_context)

    assert len(results) == 1
    score = results[0]
    assert score.debate_triggered is False
    assert score.round_2_score is None
    assert score.round_2_variance is None
    assert len(score.judges) == 3  # R1 only


@pytest.mark.asyncio
async def test_variance_above_15_triggers_round_2() -> None:
    """variance > 0.15 → debate_triggered=True; 6 entries in judges (3 R1 + 3 R2)."""
    request = _make_request(transcript=[_FakeTurn(role="agent", turn_number=1, content="ok")])
    obs_context = _build_obs_context()

    # R1 wide spread: 0.9 / 0.7 / 0.4 → variance = 0.5 > 0.15
    # R2 converged: 0.7 / 0.7 / 0.65 → variance = 0.05 < 0.10
    grade_iter = {
        "sonnet": iter(
            [
                _make_opinion(judge_id="sonnet", score=0.9, weight=0.4, round_n=1),
                _make_opinion(judge_id="sonnet", score=0.7, weight=0.4, round_n=2),
            ]
        ),
        "gpt4o": iter(
            [
                _make_opinion(judge_id="gpt4o", score=0.7, weight=0.4, round_n=1),
                _make_opinion(judge_id="gpt4o", score=0.7, weight=0.4, round_n=2),
            ]
        ),
        "kimi": iter(
            [
                _make_opinion(judge_id="kimi", score=0.4, weight=0.2, round_n=1),
                _make_opinion(judge_id="kimi", score=0.65, weight=0.2, round_n=2),
            ]
        ),
    }

    def _adapter(jid: str) -> Any:
        a = MagicMock()
        a.grade = AsyncMock(side_effect=lambda *args, **kwargs: next(grade_iter[jid]))
        return a

    adapters = {jid: _adapter(jid) for jid in ("sonnet", "gpt4o", "kimi")}

    with (
        patch.object(me, "get_judge", side_effect=lambda jid: adapters[jid]),
        patch.object(me, "build_judge_prompt", return_value=[{"role": "system", "content": "ok"}]),
        patch.object(me, "cache_lookup", AsyncMock(return_value=None)),
        patch.object(me, "cache_persist", AsyncMock(return_value=None)),
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)),
        patch.object(me, "_get_rubric_version", return_value=1),
    ):
        results = await me.grade_transcript_maj_eval(request, session=_build_session(), obs_context=obs_context)

    score = results[0]
    assert score.debate_triggered is True
    assert score.round_2_score is not None
    assert score.round_2_variance is not None
    assert score.round_2_variance < 0.10  # converged
    assert score.unconverged is False
    assert len(score.judges) == 6  # 3 R1 + 3 R2


@pytest.mark.asyncio
async def test_round_2_uses_peer_only_prompts() -> None:
    """DQ3 anti-anchoring: build_judge_prompt for judge X in R2 NEVER includes X's own R1 reasoning.

    Verifies via the call args to build_judge_prompt — peer_reasoning passed for each judge
    must exclude the entry whose judge_id matches.
    """
    request = _make_request(transcript=[_FakeTurn(role="agent", turn_number=1, content="ok")])
    obs_context = _build_obs_context()

    # Force R1 variance > 0.15 to trigger R2
    grade_iter = {
        "sonnet": iter(
            [
                _make_opinion(judge_id="sonnet", score=0.9, weight=0.4, reasoning="sonnet-r1", round_n=1),
                _make_opinion(judge_id="sonnet", score=0.7, weight=0.4, round_n=2),
            ]
        ),
        "gpt4o": iter(
            [
                _make_opinion(judge_id="gpt4o", score=0.5, weight=0.4, reasoning="gpt4o-r1", round_n=1),
                _make_opinion(judge_id="gpt4o", score=0.6, weight=0.4, round_n=2),
            ]
        ),
        "kimi": iter(
            [
                _make_opinion(judge_id="kimi", score=0.3, weight=0.2, reasoning="kimi-r1", round_n=1),
                _make_opinion(judge_id="kimi", score=0.55, weight=0.2, round_n=2),
            ]
        ),
    }

    def _adapter(jid: str) -> Any:
        a = MagicMock()
        a.grade = AsyncMock(side_effect=lambda *args, **kwargs: next(grade_iter[jid]))
        return a

    adapters = {jid: _adapter(jid) for jid in ("sonnet", "gpt4o", "kimi")}

    captured_calls: list[dict[str, Any]] = []

    def _capture_prompt(**kwargs: Any) -> list[dict[str, str]]:
        captured_calls.append(kwargs)
        return [{"role": "system", "content": "ok"}]

    with (
        patch.object(me, "get_judge", side_effect=lambda jid: adapters[jid]),
        patch.object(me, "build_judge_prompt", side_effect=_capture_prompt),
        patch.object(me, "cache_lookup", AsyncMock(return_value=None)),
        patch.object(me, "cache_persist", AsyncMock(return_value=None)),
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)),
        patch.object(me, "_get_rubric_version", return_value=1),
    ):
        await me.grade_transcript_maj_eval(request, session=_build_session(), obs_context=obs_context)

    # 3 R1 + 3 R2 = 6 prompt builds. Inspect the R2 ones (round_n=2).
    r2_calls = [c for c in captured_calls if c.get("round_n") == 2]
    assert len(r2_calls) == 3, f"Expected 3 R2 prompt builds, got {len(r2_calls)}"

    # For each R2 call, peer_reasoning MUST NOT contain the judge's own id
    for call in r2_calls:
        own_jid = call["judge_id"]
        peer = call.get("peer_reasoning") or []
        peer_ids = [entry[0] for entry in peer]
        assert own_jid not in peer_ids, (
            f"DQ3 anti-anchoring violation: judge {own_jid!r} R2 prompt contains its own R1 reasoning"
        )
        # Should have 2 peers (other judges with R1 score not None)
        assert len(peer_ids) == 2


@pytest.mark.asyncio
async def test_round_2_convergence_below_10_returns_r2_avg() -> None:
    """R2 variance ≤ 0.10 → final_score = round_2_weighted_avg, unconverged=False."""
    request = _make_request(transcript=[_FakeTurn(role="agent", turn_number=1, content="ok")])
    obs_context = _build_obs_context()

    # R1 spread, R2 converged tight (<0.10)
    grade_iter = {
        "sonnet": iter(
            [
                _make_opinion(judge_id="sonnet", score=0.9, weight=0.4, round_n=1),
                _make_opinion(judge_id="sonnet", score=0.7, weight=0.4, round_n=2),
            ]
        ),
        "gpt4o": iter(
            [
                _make_opinion(judge_id="gpt4o", score=0.6, weight=0.4, round_n=1),
                _make_opinion(judge_id="gpt4o", score=0.7, weight=0.4, round_n=2),
            ]
        ),
        "kimi": iter(
            [
                _make_opinion(judge_id="kimi", score=0.4, weight=0.2, round_n=1),
                _make_opinion(judge_id="kimi", score=0.72, weight=0.2, round_n=2),
            ]
        ),
    }

    def _adapter(jid: str) -> Any:
        a = MagicMock()
        a.grade = AsyncMock(side_effect=lambda *args, **kwargs: next(grade_iter[jid]))
        return a

    adapters = {jid: _adapter(jid) for jid in ("sonnet", "gpt4o", "kimi")}

    with (
        patch.object(me, "get_judge", side_effect=lambda jid: adapters[jid]),
        patch.object(me, "build_judge_prompt", return_value=[{"role": "system", "content": "ok"}]),
        patch.object(me, "cache_lookup", AsyncMock(return_value=None)),
        patch.object(me, "cache_persist", AsyncMock(return_value=None)),
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)),
        patch.object(me, "_get_rubric_version", return_value=1),
    ):
        results = await me.grade_transcript_maj_eval(request, session=_build_session(), obs_context=obs_context)

    score = results[0]
    assert score.unconverged is False
    # final_score = R2 weighted avg = 0.7*0.4 + 0.7*0.4 + 0.72*0.2 = 0.28 + 0.28 + 0.144 = 0.704
    assert score.final_score == pytest.approx(0.704)
    assert score.round_2_score == pytest.approx(0.704)


@pytest.mark.asyncio
async def test_round_2_unconverged_above_10_marks_unconverged_true() -> None:
    """R2 variance ≥ 0.10 → unconverged=True, final_score = round_1_weighted_avg fallback."""
    request = _make_request(transcript=[_FakeTurn(role="agent", turn_number=1, content="ok")])
    obs_context = _build_obs_context()

    # R1 wide, R2 still wide (variance ≥ 0.10)
    grade_iter = {
        "sonnet": iter(
            [
                _make_opinion(judge_id="sonnet", score=0.9, weight=0.4, round_n=1),
                _make_opinion(judge_id="sonnet", score=0.85, weight=0.4, round_n=2),
            ]
        ),
        "gpt4o": iter(
            [
                _make_opinion(judge_id="gpt4o", score=0.6, weight=0.4, round_n=1),
                _make_opinion(judge_id="gpt4o", score=0.6, weight=0.4, round_n=2),
            ]
        ),
        "kimi": iter(
            [
                _make_opinion(judge_id="kimi", score=0.3, weight=0.2, round_n=1),
                _make_opinion(judge_id="kimi", score=0.4, weight=0.2, round_n=2),
            ]
        ),
    }

    def _adapter(jid: str) -> Any:
        a = MagicMock()
        a.grade = AsyncMock(side_effect=lambda *args, **kwargs: next(grade_iter[jid]))
        return a

    adapters = {jid: _adapter(jid) for jid in ("sonnet", "gpt4o", "kimi")}

    with (
        patch.object(me, "get_judge", side_effect=lambda jid: adapters[jid]),
        patch.object(me, "build_judge_prompt", return_value=[{"role": "system", "content": "ok"}]),
        patch.object(me, "cache_lookup", AsyncMock(return_value=None)),
        patch.object(me, "cache_persist", AsyncMock(return_value=None)),
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)),
        patch.object(me, "_get_rubric_version", return_value=1),
    ):
        results = await me.grade_transcript_maj_eval(request, session=_build_session(), obs_context=obs_context)

    score = results[0]
    assert score.unconverged is True
    assert score.debate_triggered is True
    # R2 variance = 0.85 - 0.4 = 0.45 ≥ 0.10
    assert score.round_2_variance is not None
    assert score.round_2_variance >= 0.10
    # final_score per D4: fallback to round_1_weighted_avg = 0.9*0.4 + 0.6*0.4 + 0.3*0.2 = 0.36 + 0.24 + 0.06 = 0.66
    assert score.final_score == pytest.approx(0.66)


@pytest.mark.asyncio
async def test_r2_partial_one_judge_timeout_marks_partial() -> None:
    """DQ6: judge fails R2 (score=None) → use R1 score for that judge + r2_partial=True."""
    request = _make_request(transcript=[_FakeTurn(role="agent", turn_number=1, content="ok")])
    obs_context = _build_obs_context()

    # R1 variance > 0.15 (force debate); R2 kimi fails (score=None)
    grade_iter = {
        "sonnet": iter(
            [
                _make_opinion(judge_id="sonnet", score=0.9, weight=0.4, round_n=1),
                _make_opinion(judge_id="sonnet", score=0.75, weight=0.4, round_n=2),
            ]
        ),
        "gpt4o": iter(
            [
                _make_opinion(judge_id="gpt4o", score=0.5, weight=0.4, round_n=1),
                _make_opinion(judge_id="gpt4o", score=0.7, weight=0.4, round_n=2),
            ]
        ),
        "kimi": iter(
            [
                _make_opinion(judge_id="kimi", score=0.3, weight=0.2, round_n=1, reasoning="kimi-r1"),
                _make_opinion(
                    judge_id="kimi",
                    score=None,  # judge fail R2
                    weight=0.2,
                    round_n=2,
                    reasoning="judge_failed: TimeoutError",
                ),
            ]
        ),
    }

    def _adapter(jid: str) -> Any:
        a = MagicMock()
        a.grade = AsyncMock(side_effect=lambda *args, **kwargs: next(grade_iter[jid]))
        return a

    adapters = {jid: _adapter(jid) for jid in ("sonnet", "gpt4o", "kimi")}

    with (
        patch.object(me, "get_judge", side_effect=lambda jid: adapters[jid]),
        patch.object(me, "build_judge_prompt", return_value=[{"role": "system", "content": "ok"}]),
        patch.object(me, "cache_lookup", AsyncMock(return_value=None)),
        patch.object(me, "cache_persist", AsyncMock(return_value=None)),
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)),
        patch.object(me, "_get_rubric_version", return_value=1),
    ):
        results = await me.grade_transcript_maj_eval(request, session=_build_session(), obs_context=obs_context)

    score = results[0]
    assert score.r2_partial is True
    assert score.debate_triggered is True


# ──────────────────────────────────────────────────────────────────────────────
# Suspicious flag (DQ8)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_suspicious_flag_when_score_1_with_injection_attempt() -> None:
    """DQ8: all 3 judges score=1.0 + ANY injection_attempt_detected → suspicious=True."""
    request = _make_request(transcript=[_FakeTurn(role="agent", turn_number=1, content="ok")])
    obs_context = _build_obs_context()

    def _adapter(jid: str, inj: bool = False) -> Any:
        a = MagicMock()
        a.grade = AsyncMock(
            return_value=_make_opinion(
                judge_id=jid,
                score=1.0,
                weight=me.JUDGE_WEIGHTS[jid],
                injection_attempt_detected=inj,
            ),
        )
        return a

    adapters = {
        "sonnet": _adapter("sonnet", inj=True),  # injection flagged
        "gpt4o": _adapter("gpt4o"),
        "kimi": _adapter("kimi"),
    }

    with (
        patch.object(me, "get_judge", side_effect=lambda jid: adapters[jid]),
        patch.object(me, "build_judge_prompt", return_value=[{"role": "system", "content": "ok"}]),
        patch.object(me, "cache_lookup", AsyncMock(return_value=None)),
        patch.object(me, "cache_persist", AsyncMock(return_value=None)),
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)),
        patch.object(me, "_get_rubric_version", return_value=1),
    ):
        results = await me.grade_transcript_maj_eval(request, session=_build_session(), obs_context=obs_context)

    score = results[0]
    assert score.suspicious is True
    assert score.injection_attempt_detected is True


# ──────────────────────────────────────────────────────────────────────────────
# Cache integration
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cache_hit_short_circuits_judge_calls() -> None:
    """cache_lookup returns cached MajEvalScore → grade_transcript_maj_eval returns it without judge calls."""
    request = _make_request(transcript=[_FakeTurn(role="agent", turn_number=1, content="ok")])
    obs_context = _build_obs_context()

    cached_score = MajEvalScore(
        simulation_id=request.simulation_id,
        turn_n=1,
        rubric_id="voice-fidelity",
        rubric_version=1,
        tenant_slug="tenant_demo",
        persona_kind="happy",
        actor_profile_id="actor_happy_001",
        judges=[_make_opinion(judge_id="sonnet", score=0.85, weight=0.4)],
        round_1_score=0.85,
        final_score=0.85,
        round_1_variance=0.0,
        cost_usd_total=Decimal("0.001"),
        latency_ms_total=100,
        cache_hit_count=1,
        created_at=datetime.now(timezone.utc),
    )

    judge_mock = MagicMock()
    judge_mock.grade = AsyncMock(return_value=_make_opinion(judge_id="sonnet", score=0.0, weight=0.4))

    with (
        patch.object(me, "get_judge", return_value=judge_mock),
        patch.object(me, "build_judge_prompt", return_value=[{"role": "system", "content": "ok"}]),
        patch.object(me, "cache_lookup", AsyncMock(return_value=cached_score)),
        patch.object(me, "cache_persist", AsyncMock(return_value=None)) as cache_persist_mock,
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)) as persist_mock,
        patch.object(me, "_get_rubric_version", return_value=1),
    ):
        results = await me.grade_transcript_maj_eval(request, session=_build_session(), obs_context=obs_context)

    assert len(results) == 1
    assert results[0] is cached_score
    judge_mock.grade.assert_not_called()
    cache_persist_mock.assert_not_awaited()
    persist_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_cache_miss_computes_then_persists() -> None:
    """cache_lookup → None → judges invoked → cache_persist + _persist_grade called."""
    request = _make_request(transcript=[_FakeTurn(role="agent", turn_number=1, content="ok")])
    obs_context = _build_obs_context()

    def _adapter(jid: str, score: float) -> Any:
        a = MagicMock()
        a.grade = AsyncMock(
            return_value=_make_opinion(judge_id=jid, score=score, weight=me.JUDGE_WEIGHTS[jid]),
        )
        return a

    adapters = {"sonnet": _adapter("sonnet", 0.85), "gpt4o": _adapter("gpt4o", 0.83), "kimi": _adapter("kimi", 0.80)}

    with (
        patch.object(me, "get_judge", side_effect=lambda jid: adapters[jid]),
        patch.object(me, "build_judge_prompt", return_value=[{"role": "system", "content": "ok"}]),
        patch.object(me, "cache_lookup", AsyncMock(return_value=None)) as lookup_mock,
        patch.object(me, "cache_persist", AsyncMock(return_value=None)) as persist_cache_mock,
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)) as persist_grade_mock,
        patch.object(me, "_get_rubric_version", return_value=1),
    ):
        results = await me.grade_transcript_maj_eval(request, session=_build_session(), obs_context=obs_context)

    assert len(results) == 1
    lookup_mock.assert_awaited_once()
    persist_cache_mock.assert_awaited_once()
    persist_grade_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_cache_bypass_policy_skips_lookup() -> None:
    """cache_policy='bypass' → cache_lookup never called."""
    request = _make_request(transcript=[_FakeTurn(role="agent", turn_number=1, content="ok")], cache_policy="bypass")
    obs_context = _build_obs_context()

    def _adapter(jid: str, score: float) -> Any:
        a = MagicMock()
        a.grade = AsyncMock(
            return_value=_make_opinion(judge_id=jid, score=score, weight=me.JUDGE_WEIGHTS[jid]),
        )
        return a

    adapters = {"sonnet": _adapter("sonnet", 0.85), "gpt4o": _adapter("gpt4o", 0.83), "kimi": _adapter("kimi", 0.80)}

    with (
        patch.object(me, "get_judge", side_effect=lambda jid: adapters[jid]),
        patch.object(me, "build_judge_prompt", return_value=[{"role": "system", "content": "ok"}]),
        patch.object(me, "cache_lookup", AsyncMock(return_value=None)) as lookup_mock,
        patch.object(me, "cache_persist", AsyncMock(return_value=None)),
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)),
        patch.object(me, "_get_rubric_version", return_value=1),
    ):
        await me.grade_transcript_maj_eval(request, session=_build_session(), obs_context=obs_context)
        # Capture the await count INSIDE the with block (defensive — mock state
        # outside the context manager can be reset by lifecycle hooks).
        await_count = lookup_mock.await_count

    assert await_count == 0, f"cache_policy='bypass' must skip cache_lookup; awaited {await_count} times"


# ──────────────────────────────────────────────────────────────────────────────
# Cost + latency aggregation
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cost_aggregation_sums_per_judge() -> None:
    """MajEvalScore.cost_usd_total = sum of per-judge cost_usd; latency_ms_total likewise."""
    request = _make_request(transcript=[_FakeTurn(role="agent", turn_number=1, content="ok")])
    obs_context = _build_obs_context()

    def _adapter(jid: str, cost: Decimal, latency: int) -> Any:
        a = MagicMock()
        a.grade = AsyncMock(
            return_value=_make_opinion(
                judge_id=jid,
                score=0.85,
                weight=me.JUDGE_WEIGHTS[jid],
                cost_usd=cost,
                latency_ms=latency,
            ),
        )
        return a

    adapters = {
        "sonnet": _adapter("sonnet", Decimal("0.005"), 200),
        "gpt4o": _adapter("gpt4o", Decimal("0.003"), 150),
        "kimi": _adapter("kimi", Decimal("0.001"), 100),
    }

    with (
        patch.object(me, "get_judge", side_effect=lambda jid: adapters[jid]),
        patch.object(me, "build_judge_prompt", return_value=[{"role": "system", "content": "ok"}]),
        patch.object(me, "cache_lookup", AsyncMock(return_value=None)),
        patch.object(me, "cache_persist", AsyncMock(return_value=None)),
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)),
        patch.object(me, "_get_rubric_version", return_value=1),
    ):
        results = await me.grade_transcript_maj_eval(request, session=_build_session(), obs_context=obs_context)

    score = results[0]
    # Verify cost aggregation: 0.005 + 0.003 + 0.001 = 0.009 USD
    assert score.cost_usd_total == Decimal("0.009")
    # Verify latency aggregation: 200 + 150 + 100 = 450 ms
    assert score.latency_ms_total == 450


# ──────────────────────────────────────────────────────────────────────────────
# Concurrency cap (Semaphore)
# ──────────────────────────────────────────────────────────────────────────────


def test_judge_concurrency_constant_is_20() -> None:
    """D17 cement: JUDGE_CONCURRENCY = 20 (Semaphore cap on parallel judge calls)."""
    assert me.JUDGE_CONCURRENCY == 20


def test_variance_r1_threshold_is_0_15() -> None:
    """D3 cement: VARIANCE_R1_THRESHOLD = 0.15 (Round 2 trigger)."""
    assert me.VARIANCE_R1_THRESHOLD == 0.15


def test_variance_r2_target_is_0_10() -> None:
    """D4 cement: VARIANCE_R2_TARGET = 0.10 (R2 convergence target)."""
    assert me.VARIANCE_R2_TARGET == 0.10


# ──────────────────────────────────────────────────────────────────────────────
# Orchestration: per-rubric per-turn matrix
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_orchestration_per_rubric_per_turn() -> None:
    """3 rubrics x 4 turns = 12 MajEvalScore rows produced."""
    transcript = [
        _FakeTurn(role="customer", turn_number=1, content="hi"),
        _FakeTurn(role="agent", turn_number=2, content="hola"),
        _FakeTurn(role="customer", turn_number=3, content="ok"),
        _FakeTurn(role="agent", turn_number=4, content="dime"),
    ]
    request = _make_request(
        transcript=transcript,
        rubrics=["voice-fidelity", "no-overpromise", "no-hallucination"],
    )
    obs_context = _build_obs_context()

    def _adapter(jid: str) -> Any:
        a = MagicMock()
        a.grade = AsyncMock(
            return_value=_make_opinion(judge_id=jid, score=0.85, weight=me.JUDGE_WEIGHTS[jid]),
        )
        return a

    adapters = {jid: _adapter(jid) for jid in ("sonnet", "gpt4o", "kimi")}

    with (
        patch.object(me, "get_judge", side_effect=lambda jid: adapters[jid]),
        patch.object(me, "build_judge_prompt", return_value=[{"role": "system", "content": "ok"}]),
        patch.object(me, "cache_lookup", AsyncMock(return_value=None)),
        patch.object(me, "cache_persist", AsyncMock(return_value=None)),
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)),
        patch.object(me, "_get_rubric_version", return_value=1),
    ):
        results = await me.grade_transcript_maj_eval(request, session=_build_session(), obs_context=obs_context)

    assert len(results) == 4 * 3  # 4 turns x 3 rubrics
    rubric_ids = {r.rubric_id for r in results}
    assert rubric_ids == {"voice-fidelity", "no-overpromise", "no-hallucination"}
    turn_ns = {r.turn_n for r in results}
    assert turn_ns == {1, 2, 3, 4}


# ──────────────────────────────────────────────────────────────────────────────
# <2 valid judges defense
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_lt_2_valid_judges_unconverged_score_null() -> None:
    """If <2 judges return valid scores → unconverged=True per fallback contract."""
    request = _make_request(transcript=[_FakeTurn(role="agent", turn_number=1, content="ok")])
    obs_context = _build_obs_context()

    # 2 of 3 judges fail (score=None); only sonnet returns valid score.
    def _adapter(jid: str, score: float | None) -> Any:
        a = MagicMock()
        a.grade = AsyncMock(
            return_value=_make_opinion(
                judge_id=jid,
                score=score,
                weight=me.JUDGE_WEIGHTS[jid],
                reasoning="fail" if score is None else "ok",
            ),
        )
        return a

    adapters = {
        "sonnet": _adapter("sonnet", 0.85),
        "gpt4o": _adapter("gpt4o", None),
        "kimi": _adapter("kimi", None),
    }

    with (
        patch.object(me, "get_judge", side_effect=lambda jid: adapters[jid]),
        patch.object(me, "build_judge_prompt", return_value=[{"role": "system", "content": "ok"}]),
        patch.object(me, "cache_lookup", AsyncMock(return_value=None)),
        patch.object(me, "cache_persist", AsyncMock(return_value=None)),
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)),
        patch.object(me, "_get_rubric_version", return_value=1),
    ):
        results = await me.grade_transcript_maj_eval(request, session=_build_session(), obs_context=obs_context)

    score = results[0]
    assert score.unconverged is True
    # final_score may be 0.0 (no valid weighted average) per fallback


# ──────────────────────────────────────────────────────────────────────────────
# PII sanitization defense-in-depth (D10)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pii_sanitize_called_pre_judge() -> None:
    """sanitize_payload invoked over each transcript turn BEFORE any judge call."""
    request = _make_request(transcript=[_FakeTurn(role="agent", turn_number=1, content="my email is x@y.com")])
    obs_context = _build_obs_context()

    def _adapter(jid: str) -> Any:
        a = MagicMock()
        a.grade = AsyncMock(
            return_value=_make_opinion(judge_id=jid, score=0.85, weight=me.JUDGE_WEIGHTS[jid]),
        )
        return a

    adapters = {jid: _adapter(jid) for jid in ("sonnet", "gpt4o", "kimi")}

    sanitize_calls: list[Any] = []

    def _track_sanitize(payload: dict[str, Any]) -> dict[str, Any]:
        sanitize_calls.append(payload)
        return payload  # passthrough for unit test

    with (
        patch.object(me, "get_judge", side_effect=lambda jid: adapters[jid]),
        patch.object(me, "build_judge_prompt", return_value=[{"role": "system", "content": "ok"}]),
        patch.object(me, "cache_lookup", AsyncMock(return_value=None)),
        patch.object(me, "cache_persist", AsyncMock(return_value=None)),
        patch.object(me, "_persist_grade", AsyncMock(return_value=None)),
        patch.object(me, "_get_rubric_version", return_value=1),
        patch.object(me, "sanitize_payload", side_effect=_track_sanitize),
    ):
        await me.grade_transcript_maj_eval(request, session=_build_session(), obs_context=obs_context)

    # sanitize_payload called at least once for the transcript turn(s) BEFORE judge calls
    assert len(sanitize_calls) >= 1, "sanitize_payload not called in grade_transcript_maj_eval"
