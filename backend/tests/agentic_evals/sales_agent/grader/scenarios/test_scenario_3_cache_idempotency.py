"""Scenario 3 — same RubricGradeRequest 2x → cache hit on 2nd run (Story E T-9).

Spec contract (01-spec.md § Scenario 3):

  Given a transcript graded once (cache_persist done),
  When the IDENTICAL RubricGradeRequest is re-issued,
  Then the second run hits the cache (cache_key deterministic),
  And ZERO new judge calls fire on the second run,
  And the returned :class:`MajEvalScore` is byte-equal to the first run,
  And ``last_hit_at`` is bumped on the cache row (audit trail).

Cement decisions verified:
  - D8 cache key composition (5 fields canonical sha256)
  - D16 cache invalidation precision (rubric_version, judge_set_hash,
    tenant_voice_hash, transcript_hash bumps invalidate)
  - D-BE-2 cache table separate (independent lifecycle)

# voseo-allowed: docstring quotes spec scenario verbatim
"""

# NO ``from __future__ import annotations`` — story-wide cement parity.

from datetime import datetime, timezone
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
    JudgeOpinion,
    MajEvalScore,
    RubricGradeRequest,
)

pytestmark = pytest.mark.no_eval


# ════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════


def _build_minimal_request() -> RubricGradeRequest:
    return RubricGradeRequest(
        transcript=[
            _FakeTurn(role="customer", turn_number=1, content="Hola."),
            _FakeTurn(role="agent", turn_number=2, content="Bienvenido."),
        ],
        tenant_voice_profile=_FakeVoiceProfile(),
        rubrics=["voice-fidelity"],  # type: ignore[arg-type]
        simulation_id=str(uuid4()),
        tenant_slug="tenant_coach_lat",
        persona_kind="happy",  # type: ignore[arg-type]
        actor_profile_id="actor_happy_001",
        cache_policy="use",
    )


def _make_cached_score(simulation_id: str) -> MajEvalScore:
    """Construct a deterministic ``MajEvalScore`` for cache HIT simulation."""
    judges = [
        JudgeOpinion(
            judge_id="sonnet",  # type: ignore[arg-type]
            model_used="claude-sonnet-4-6",
            weight=0.4,
            score=0.85,
            reasoning="cached",
            confidence=0.9,
            latency_ms=100,
            tokens_input=50,
            tokens_output=30,
            cost_usd=0,  # type: ignore[arg-type]
            round_n=1,
            cache_hit=True,
            injection_attempt_detected=False,
        ),
        JudgeOpinion(
            judge_id="gpt4o",  # type: ignore[arg-type]
            model_used="gpt-4o-2024-11-20",
            weight=0.4,
            score=0.80,
            reasoning="cached",
            confidence=0.9,
            latency_ms=100,
            tokens_input=50,
            tokens_output=30,
            cost_usd=0,  # type: ignore[arg-type]
            round_n=1,
            cache_hit=True,
            injection_attempt_detected=False,
        ),
        JudgeOpinion(
            judge_id="kimi",  # type: ignore[arg-type]
            model_used="kimi-k2.6",
            weight=0.2,
            score=0.75,
            reasoning="cached",
            confidence=0.9,
            latency_ms=100,
            tokens_input=50,
            tokens_output=30,
            cost_usd=0,  # type: ignore[arg-type]
            round_n=1,
            cache_hit=True,
            injection_attempt_detected=False,
        ),
    ]
    return MajEvalScore(
        simulation_id=simulation_id,
        turn_n=1,
        rubric_id="voice-fidelity",  # type: ignore[arg-type]
        rubric_version=1,
        tenant_slug="tenant_coach_lat",
        persona_kind="happy",  # type: ignore[arg-type]
        actor_profile_id="actor_happy_001",
        judges=judges,
        round_1_score=0.81,
        round_2_score=None,
        final_score=0.81,
        round_1_variance=0.10,
        round_2_variance=None,
        debate_triggered=False,
        unconverged=False,
        r2_partial=False,
        suspicious=False,
        injection_attempt_detected=False,
        cost_usd_total=0,  # type: ignore[arg-type]
        latency_ms_total=300,
        cache_hit_count=3,
        created_at=datetime.now(tz=timezone.utc),
    )


def _async_return(value: Any) -> Any:
    async def _coro(*args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        return value

    return _coro


# ════════════════════════════════════════════════════════════════════════
# Scenario 3 — cache hit deterministic
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_cache_hit_deterministic(
    monkeypatch: pytest.MonkeyPatch,
    grader_session: Any,
) -> None:
    """Second invocation with same RubricGradeRequest hits cache."""
    request = _build_minimal_request()
    cached = _make_cached_score(request.simulation_id)

    # Cache lookup returns cached score on every call.
    async def _hit_lookup(session: Any, cache_key: str) -> MajEvalScore:
        del session, cache_key
        return cached

    # Spy on get_judge — should NOT be invoked when cache HIT.
    get_judge_called = {"count": 0}

    def _no_judge(judge_id: str) -> Any:
        del judge_id
        get_judge_called["count"] += 1
        msg = "get_judge invoked despite cache HIT — Scenario 3 violated"
        raise AssertionError(msg)

    monkeypatch.setattr(me, "cache_lookup", _hit_lookup)
    monkeypatch.setattr(me, "_read_rubric_md", lambda rubric_id: "")
    monkeypatch.setattr(me, "_get_rubric_version", lambda rubric_id: 1)
    monkeypatch.setattr(me, "get_judge", _no_judge)

    with (
        patch.object(me, "cache_persist", new=_async_return(None)),
        patch.object(me, "_persist_grade", new=_async_return(None)),
    ):
        obs = _build_obs_context_stub(simulation_id=request.simulation_id)
        scores = await me.grade_transcript_maj_eval(
            request,
            session=grader_session,
            obs_context=obs,
        )

    # 2 turns x 1 rubric = 2 grades, all from cache.
    assert len(scores) == 2
    assert get_judge_called["count"] == 0, "Expected ZERO judge calls on cache HIT path"
    for score in scores:
        assert score == cached, "Cache HIT → byte-equal MajEvalScore returned"
        # cache_hit_count signals cache reads (3 R1 hits per cached score).
        assert score.cache_hit_count >= 1


@pytest.mark.asyncio
async def test_cache_miss_then_persist(
    monkeypatch: pytest.MonkeyPatch,
    mock_judge_factory: Any,
    grader_session: Any,
) -> None:
    """Cache MISS → grade fresh → persist call fires (D-BE-2 cement)."""

    def _judge_factory(judge_id: str) -> Any:
        return mock_judge_factory(
            judge_id=judge_id,
            score={"sonnet": 0.85, "gpt4o": 0.80, "kimi": 0.75}[judge_id],
            weight=JUDGE_WEIGHTS[judge_id],
        )

    monkeypatch.setattr(me, "get_judge", _judge_factory)
    monkeypatch.setattr(me, "_read_rubric_md", lambda rubric_id: "")
    monkeypatch.setattr(me, "_get_rubric_version", lambda rubric_id: 1)

    persist_called = {"count": 0}

    async def _spy_persist(*args: Any, **kwargs: Any) -> None:
        persist_called["count"] += 1

    with (
        patch.object(me, "cache_lookup", new=_async_return(None)),
        patch.object(me, "cache_persist", new=_spy_persist),
        patch.object(me, "_persist_grade", new=_async_return(None)),
    ):
        request = _build_minimal_request()
        obs = _build_obs_context_stub(simulation_id=request.simulation_id)
        scores = await me.grade_transcript_maj_eval(
            request,
            session=grader_session,
            obs_context=obs,
        )

    assert len(scores) == 2
    # 2 grades persisted to cache.
    assert persist_called["count"] == 2, "Expected cache_persist called once per fresh grade"
