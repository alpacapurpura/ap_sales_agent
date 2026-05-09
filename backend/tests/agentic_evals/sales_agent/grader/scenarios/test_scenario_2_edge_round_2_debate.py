"""Scenario 2 — variance > 0.15 triggers Round 2 debate (Story E T-9).

Spec contract (01-spec.md § Scenario 2):

  Given a transcript where 3 judges Round 1 disagree (variance > 0.15),
  When ``grade_transcript_maj_eval`` runs,
  Then debate_triggered=True,
  And Round 2 prompts include OTHER 2 judges' R1 reasoning ONLY (DQ3 cement),
  And Round 2 variance < 0.10 → unconverged=False (convergence path),
    OR Round 2 variance ≥ 0.10 → unconverged=True + final_score=R1_weighted_avg.
  And r2_partial=True only when ≥1 judge fails R2 (DQ6 cement).

Cement decisions verified:
  - D3 variance threshold 0.15 (max-min)
  - D4 unconverged fallback to R1 weighted avg
  - DQ3 anti-anchoring (peer-only reasoning)
  - DQ6 r2_partial fallback (judge fail R2 → R1 score for that judge)
  - DQ8 unconverged → structlog warn, NOT auto-block

# voseo-allowed: docstring quotes spec scenario verbatim
"""

# NO ``from __future__ import annotations`` — story-wide cement parity.

from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest

from tests.agentic_evals.sales_agent.grader._internal import maj_eval as me
from tests.agentic_evals.sales_agent.grader._internal.judge_registry import JUDGE_WEIGHTS
from tests.agentic_evals.sales_agent.grader.conftest import (
    _FakeTurn,
    _FakeVoiceProfile,
    _build_obs_context_stub,
)
from tests.agentic_evals.sales_agent.grader.result import (
    MajEvalScore,
    RubricGradeRequest,
)

pytestmark = pytest.mark.no_eval


# ════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════


def _build_request_minimal_2_turns() -> RubricGradeRequest:
    """Minimal 2-turn request — 1 customer + 1 agent."""
    return RubricGradeRequest(
        transcript=[
            _FakeTurn(role="customer", turn_number=1, content="¿Tienen garantía?"),
            _FakeTurn(role="agent", turn_number=2, content="Permíteme confirmarlo y te aviso."),
        ],
        tenant_voice_profile=_FakeVoiceProfile(),
        rubrics=["voice-fidelity"],  # type: ignore[arg-type]
        simulation_id=str(uuid4()),
        tenant_slug="tenant_coach_lat",
        persona_kind="nurture",  # type: ignore[arg-type]
        actor_profile_id="actor_nurture_001",
        cache_policy="bypass",
    )


def _factory_round1_diverged_round2_converged(mock_judge_factory: Any) -> Any:
    """Round 1 variance > 0.15 → Round 2 converges (variance < 0.10).

    Round 1 scores: sonnet=0.90, gpt4o=0.50, kimi=0.40 → variance=0.50 → debate.
    Round 2 scores: sonnet=0.65, gpt4o=0.60, kimi=0.58 → variance=0.07 < 0.10.
    """

    def _factory(judge_id: str) -> Any:
        round_scores = {
            "sonnet": [0.90, 0.65],
            "gpt4o": [0.50, 0.60],
            "kimi": [0.40, 0.58],
        }
        return mock_judge_factory(
            judge_id=judge_id,
            score=round_scores[judge_id],
            weight=JUDGE_WEIGHTS[judge_id],
            reasoning=f"{judge_id} reasoning sample",
        )

    return _factory


def _factory_round1_diverged_round2_unconverged(mock_judge_factory: Any) -> Any:
    """Round 1 variance > 0.15 → Round 2 still > 0.10 (unconverged path)."""

    def _factory(judge_id: str) -> Any:
        round_scores = {
            "sonnet": [0.90, 0.85],
            "gpt4o": [0.50, 0.55],
            "kimi": [0.40, 0.45],
        }
        return mock_judge_factory(
            judge_id=judge_id,
            score=round_scores[judge_id],
            weight=JUDGE_WEIGHTS[judge_id],
            reasoning=f"{judge_id} stuck",
        )

    return _factory


def _factory_round1_diverged_round2_one_fails(mock_judge_factory: Any) -> Any:
    """R1 diverges; R2 has 1 judge fail (score=None) → r2_partial=True."""

    def _factory(judge_id: str) -> Any:
        round_scores: dict[str, list[float | None]] = {
            "sonnet": [0.90, 0.65],
            "gpt4o": [0.50, None],  # judge fail R2
            "kimi": [0.40, 0.55],
        }
        return mock_judge_factory(
            judge_id=judge_id,
            score=round_scores[judge_id],  # type: ignore[arg-type]
            weight=JUDGE_WEIGHTS[judge_id],
            reasoning=f"{judge_id}",
        )

    return _factory


def _async_return(value: Any) -> Any:
    """Plain awaitable returning ``value``."""

    async def _coro(*args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        return value

    return _coro


# ════════════════════════════════════════════════════════════════════════
# Scenario 2 — variance triggers Round 2
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_variance_triggers_round_2(
    monkeypatch: pytest.MonkeyPatch,
    mock_judge_factory: Any,
    grader_session: Any,
) -> None:
    """R1 variance 0.50 > 0.15 → debate_triggered=True; R2 converges."""
    monkeypatch.setattr(
        me,
        "get_judge",
        _factory_round1_diverged_round2_converged(mock_judge_factory),
    )
    monkeypatch.setattr(me, "_read_rubric_md", lambda rubric_id: "")
    monkeypatch.setattr(me, "_get_rubric_version", lambda rubric_id: 1)

    with (
        patch.object(me, "cache_lookup", new=_async_return(None)),
        patch.object(me, "cache_persist", new=_async_return(None)),
        patch.object(me, "_persist_grade", new=_async_return(None)),
    ):
        request = _build_request_minimal_2_turns()
        obs = _build_obs_context_stub(simulation_id=request.simulation_id)
        scores = await me.grade_transcript_maj_eval(
            request,
            session=grader_session,
            obs_context=obs,
        )

    # 2 turns x 1 rubric = 2 grades.
    assert len(scores) == 2
    for score in scores:
        assert isinstance(score, MajEvalScore)
        assert score.debate_triggered is True
        assert score.round_1_variance > 0.15
        assert score.round_2_variance is not None
        assert score.round_2_variance < 0.10, "R2 expected to converge in this scenario"
        assert score.unconverged is False
        assert score.r2_partial is False
        # 6 judges JSONB entries (3 R1 + 3 R2).
        assert len(score.judges) == 6
        # final_score = R2 weighted avg per spec D4 (converged path).
        assert score.round_2_score is not None
        assert score.final_score == pytest.approx(score.round_2_score, abs=0.01)


@pytest.mark.asyncio
async def test_round_2_convergence_or_unconverged_flag(
    monkeypatch: pytest.MonkeyPatch,
    mock_judge_factory: Any,
    grader_session: Any,
) -> None:
    """R2 variance ≥ 0.10 → unconverged=True + final_score=R1_weighted_avg."""
    monkeypatch.setattr(
        me,
        "get_judge",
        _factory_round1_diverged_round2_unconverged(mock_judge_factory),
    )
    monkeypatch.setattr(me, "_read_rubric_md", lambda rubric_id: "")
    monkeypatch.setattr(me, "_get_rubric_version", lambda rubric_id: 1)

    with (
        patch.object(me, "cache_lookup", new=_async_return(None)),
        patch.object(me, "cache_persist", new=_async_return(None)),
        patch.object(me, "_persist_grade", new=_async_return(None)),
    ):
        request = _build_request_minimal_2_turns()
        obs = _build_obs_context_stub(simulation_id=request.simulation_id)
        scores = await me.grade_transcript_maj_eval(
            request,
            session=grader_session,
            obs_context=obs,
        )

    for score in scores:
        assert score.debate_triggered is True
        assert score.unconverged is True
        assert score.round_2_variance is not None
        assert score.round_2_variance >= 0.10
        # Fallback: final_score = R1 weighted avg (D4 cement).
        assert score.final_score == pytest.approx(score.round_1_score, abs=0.001)


@pytest.mark.asyncio
async def test_r2_partial_fallback_judge_fail(
    monkeypatch: pytest.MonkeyPatch,
    mock_judge_factory: Any,
    grader_session: Any,
) -> None:
    """R2 with 1 judge score=None → r2_partial=True + R1 fallback for that judge."""
    monkeypatch.setattr(
        me,
        "get_judge",
        _factory_round1_diverged_round2_one_fails(mock_judge_factory),
    )
    monkeypatch.setattr(me, "_read_rubric_md", lambda rubric_id: "")
    monkeypatch.setattr(me, "_get_rubric_version", lambda rubric_id: 1)

    with (
        patch.object(me, "cache_lookup", new=_async_return(None)),
        patch.object(me, "cache_persist", new=_async_return(None)),
        patch.object(me, "_persist_grade", new=_async_return(None)),
    ):
        request = _build_request_minimal_2_turns()
        obs = _build_obs_context_stub(simulation_id=request.simulation_id)
        scores = await me.grade_transcript_maj_eval(
            request,
            session=grader_session,
            obs_context=obs,
        )

    for score in scores:
        assert score.debate_triggered is True
        assert score.r2_partial is True, "1 judge failed R2 → r2_partial flag must be true"
        # R1 + R2 stored verbatim — judges JSONB has 6 entries; gpt4o R2 score=None.
        assert len(score.judges) == 6
        r2_gpt4o = next(j for j in score.judges if j.judge_id == "gpt4o" and j.round_n == 2)
        assert r2_gpt4o.score is None


@pytest.mark.asyncio
async def test_round_2_peer_reasoning_excludes_self(
    monkeypatch: pytest.MonkeyPatch,
    mock_judge_factory: Any,
    grader_session: Any,
) -> None:
    """DQ3 anti-anchoring — Round 2 prompts NEVER include own R1 reasoning."""
    monkeypatch.setattr(
        me,
        "get_judge",
        _factory_round1_diverged_round2_converged(mock_judge_factory),
    )
    monkeypatch.setattr(me, "_read_rubric_md", lambda rubric_id: "")
    monkeypatch.setattr(me, "_get_rubric_version", lambda rubric_id: 1)

    captured_calls: list[dict[str, Any]] = []
    original_build = me.build_judge_prompt

    def _spy_build(**kwargs: Any) -> Any:
        captured_calls.append(kwargs)
        return original_build(**kwargs)

    monkeypatch.setattr(me, "build_judge_prompt", _spy_build)

    with (
        patch.object(me, "cache_lookup", new=_async_return(None)),
        patch.object(me, "cache_persist", new=_async_return(None)),
        patch.object(me, "_persist_grade", new=_async_return(None)),
    ):
        request = _build_request_minimal_2_turns()
        obs = _build_obs_context_stub(simulation_id=request.simulation_id)
        await me.grade_transcript_maj_eval(
            request,
            session=grader_session,
            obs_context=obs,
        )

    # Filter to R2 calls only.
    r2_calls = [c for c in captured_calls if c.get("round_n") == 2]
    assert len(r2_calls) > 0, "Expected Round 2 prompt builder invocations"
    for call in r2_calls:
        judge_id = call["judge_id"]
        peer_reasoning = call.get("peer_reasoning") or []
        for peer_jid, _peer_score, _peer_text in peer_reasoning:
            assert peer_jid != judge_id, f"DQ3 violated — judge {judge_id!r} R2 prompt included own R1 reasoning"
