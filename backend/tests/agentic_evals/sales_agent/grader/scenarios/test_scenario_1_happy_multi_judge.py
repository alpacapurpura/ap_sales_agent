"""Scenario 1 — happy persona, 3 judges Round 1 converged → no debate (Story E T-9).

Spec contract (01-spec.md § Scenario 1):

  Given a happy customer transcript (8 turns) and 3 rubrics in scope
  (voice-fidelity + no-overpromise + no-hallucination),
  When ``grade_transcript_maj_eval`` runs,
  Then 3 judges (sonnet/gpt4o/kimi) execute Round 1 in parallel,
  And Round 1 variance (max-min) is < 0.15 → debate_triggered=False,
  And final_score = round_1_weighted_avg (D2 weights 0.4/0.4/0.2),
  And N_turns x N_rubrics = 24 MajEvalScore rows persisted.

Cement decisions verified:
  - D1 MAJ-EVAL paradigm
  - D2 weights 0.4/0.4/0.2
  - D3 variance threshold 0.15 (max-min, NOT statistical)
  - D7 happy persona → 3 rubrics
  - H7 cost-bucket invariant (judge calls write eval_simulator_llm_call ONLY)

Mock layer: ``mock_judge_factory`` returns deterministic adapters; no real LLM.
Real-LLM layer: ``@pytest.mark.eval`` + ``--run-evals`` flag (CI nightly).

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


def _make_8_turn_happy_transcript() -> list[_FakeTurn]:
    """8-turn happy customer transcript (Story D goldens shape — duck-typed)."""
    turns: list[_FakeTurn] = []
    for i in range(8):
        role = "customer" if i % 2 == 0 else "agent"
        content = (
            "Hola, vi tu anuncio."
            if i == 0
            else f"Mensaje turno {i} ({'cliente' if role == 'customer' else 'agente'}): conversación happy."
        )
        turns.append(_FakeTurn(role=role, turn_number=i, content=content))
    return turns


def _build_request_happy_3_rubrics() -> RubricGradeRequest:
    """RubricGradeRequest — happy persona, 3 rubrics."""
    return RubricGradeRequest(
        transcript=_make_8_turn_happy_transcript(),
        tenant_voice_profile=_FakeVoiceProfile(),
        rubrics=["voice-fidelity", "no-overpromise", "no-hallucination"],  # type: ignore[arg-type]
        simulation_id=str(uuid4()),
        tenant_slug="tenant_coach_lat",
        persona_kind="happy",  # type: ignore[arg-type]
        actor_profile_id="actor_happy_001",
        cache_policy="bypass",  # force fresh grading (Scenario 1 cold path)
    )


def _make_round1_converged_judge_factory(mock_judge_factory: Any) -> Any:
    """Return a side_effect callable for ``get_judge`` mocks.

    All 3 judges return scores within 0.15 of each other → no debate trigger.
    """

    def _factory(judge_id: str) -> Any:
        scores_by_judge = {"sonnet": 0.85, "gpt4o": 0.80, "kimi": 0.75}
        return mock_judge_factory(
            judge_id=judge_id,
            score=scores_by_judge[judge_id],
            weight=JUDGE_WEIGHTS[judge_id],
            reasoning=f"{judge_id}: voice fidelity high; warm tone preserved",
        )

    return _factory


def _async_return(value: Any) -> Any:
    """Plain awaitable returning ``value``."""

    async def _coro(*args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        return value

    return _coro


# ════════════════════════════════════════════════════════════════════════
# Scenario 1 — happy multi-judge Round 1 converged
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_3_rubrics_per_turn(
    monkeypatch: pytest.MonkeyPatch,
    mock_judge_factory: Any,
    grader_session: Any,
) -> None:
    """8 turns x 3 rubrics = 24 MajEvalScore rows; debate_triggered=False."""
    monkeypatch.setattr(
        me,
        "get_judge",
        _make_round1_converged_judge_factory(mock_judge_factory),
    )
    monkeypatch.setattr(me, "_read_rubric_md", lambda rubric_id: "")
    monkeypatch.setattr(me, "_get_rubric_version", lambda rubric_id: 1)

    with (
        patch.object(me, "cache_lookup", new=_async_return(None)),
        patch.object(me, "cache_persist", new=_async_return(None)),
        patch.object(me, "_persist_grade", new=_async_return(None)),
    ):
        request = _build_request_happy_3_rubrics()
        obs = _build_obs_context_stub(simulation_id=request.simulation_id)

        scores = await me.grade_transcript_maj_eval(
            request,
            session=grader_session,
            obs_context=obs,
        )

    # 8 turns x 3 rubrics = 24 grades.
    assert len(scores) == 8 * 3, f"Expected 24 grades, got {len(scores)}"

    for score in scores:
        assert isinstance(score, MajEvalScore)
        assert score.debate_triggered is False, "Round 1 converged; no debate expected"
        assert score.unconverged is False
        assert score.r2_partial is False
        # Variance max-min over (0.85, 0.80, 0.75) = 0.10 < 0.15 threshold.
        assert score.round_1_variance < 0.15
        # Weighted avg: 0.85*0.4 + 0.80*0.4 + 0.75*0.2 = 0.81
        assert score.round_1_score == pytest.approx(0.81, abs=0.01)
        assert score.final_score == score.round_1_score
        assert len(score.judges) == 3, "3 judges in Round 1 only"


@pytest.mark.asyncio
async def test_extended_eval_metadata_persona_kind_and_grader(
    monkeypatch: pytest.MonkeyPatch,
    mock_judge_factory: Any,
    grader_session: Any,
) -> None:
    """Story C/E eval_metadata extended keys reach persona_kind dispatch."""
    monkeypatch.setattr(
        me,
        "get_judge",
        _make_round1_converged_judge_factory(mock_judge_factory),
    )
    monkeypatch.setattr(me, "_read_rubric_md", lambda rubric_id: "")
    monkeypatch.setattr(me, "_get_rubric_version", lambda rubric_id: 1)

    with (
        patch.object(me, "cache_lookup", new=_async_return(None)),
        patch.object(me, "cache_persist", new=_async_return(None)),
        patch.object(me, "_persist_grade", new=_async_return(None)),
    ):
        request = _build_request_happy_3_rubrics()
        obs = _build_obs_context_stub(simulation_id=request.simulation_id)
        scores = await me.grade_transcript_maj_eval(
            request,
            session=grader_session,
            obs_context=obs,
        )

    # All scores carry persona_kind=happy + tenant_slug + actor_profile_id.
    for score in scores:
        assert score.persona_kind == "happy"
        assert score.tenant_slug == "tenant_coach_lat"
        assert score.actor_profile_id == "actor_happy_001"
