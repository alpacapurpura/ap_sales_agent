"""Conftest for the grader test suite (Story E T-9).

Re-exports two factory fixtures consumed by the scenario tests
(``test_scenario_1_*``, ``test_scenario_2_*``, ``test_scenario_3_*``,
``test_scenario_4_*``) plus the integration hook test
(``test_run_simulation_grader_hook.py``):

* ``mock_judge_factory`` — builds a ``_JudgeAdapter``-shaped mock that
  yields deterministic :class:`JudgeOpinion` instances. Avoids real LLM
  dispatch in unit tests; integration scenarios marked ``@pytest.mark.eval``
  use the real registry behind ``--run-evals``.
* ``grader_session`` — yields a stub ``AsyncSession`` (MagicMock) so
  cache + persist paths can be exercised without a live Postgres.

Both fixtures default to function scope per ``tessl__pytest-api-testing``
guideline (Default to function scope — keep tests independent).

The parent ``tests/agentic_evals/sales_agent/conftest.py`` auto-applies
``@pytest.mark.eval`` to every collected item under
``tests/agentic_evals/sales_agent/``. Tests that should run on default CI
opt out via ``pytestmark = pytest.mark.no_eval`` at module level.

Per ``.claude/rules/parallel-safety.md``: this conftest does NOT touch
the master ``backend/tests/conftest.py`` — fixtures are scoped to
``tests/agentic_evals/sales_agent/grader/`` only.

# voseo-allowed: docstring quotes Story E mandate verbatim
"""

# NO ``from __future__ import annotations`` — story-wide cement parity
# with simulator/conftest.py (Story B T-9 result.md cite).

from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.agentic_evals.sales_agent.grader.result import JudgeOpinion


# ════════════════════════════════════════════════════════════════════════
# mock_judge_factory — deterministic JudgeOpinion stubs
# ════════════════════════════════════════════════════════════════════════


JUDGE_MODELS_LOOKUP = {
    "sonnet": "claude-sonnet-4-6",
    "gpt4o": "gpt-4o-2024-11-20",
    "kimi": "kimi-k2.6",
}


def _make_opinion(
    *,
    judge_id: str,
    score: float | None,
    weight: float,
    round_n: int = 1,
    reasoning: str = "stub reasoning for test",
    confidence: float = 0.9,
    cost_usd: Decimal = Decimal("0.001"),
    latency_ms: int = 100,
    cache_hit: bool = False,
    injection_attempt_detected: bool = False,
) -> JudgeOpinion:
    """Build a JudgeOpinion with sensible defaults for unit tests."""
    return JudgeOpinion(
        judge_id=judge_id,  # type: ignore[arg-type]
        model_used=JUDGE_MODELS_LOOKUP[judge_id],
        weight=weight,
        score=score,
        reasoning=reasoning,
        confidence=confidence,
        latency_ms=latency_ms,
        tokens_input=50,
        tokens_output=30,
        cost_usd=cost_usd,
        round_n=round_n,  # type: ignore[arg-type]
        cache_hit=cache_hit,
        injection_attempt_detected=injection_attempt_detected,
    )


@pytest.fixture
def mock_judge_factory() -> Callable[..., Any]:
    """Return a factory that builds mock _JudgeAdapter instances.

    Usage::

        def test_round_1_converged(mock_judge_factory):
            adapter = mock_judge_factory(
                judge_id="sonnet",
                score=0.85,
                round_n=1,
            )
            opinion = await adapter.grade(prompt=[], weight=0.4, round_n=1, ...)
            assert opinion.score == 0.85

    The factory accepts ``score`` either as a float (deterministic
    single-round value) or as a list of floats keyed by ``round_n``
    (for Round 1 / Round 2 sequential scoring).
    """

    def _build(
        *,
        judge_id: str,
        score: float | list[float] | None = 0.85,
        weight: float = 0.4,
        reasoning: str = "stub reasoning",
        confidence: float = 0.9,
        injection_attempt_detected: bool = False,
        cache_hit: bool = False,
        cost_usd: Decimal = Decimal("0.001"),
        latency_ms: int = 100,
    ) -> Any:
        adapter = MagicMock()
        adapter.judge_id = judge_id
        adapter.model = JUDGE_MODELS_LOOKUP[judge_id]

        if isinstance(score, list):
            scores_per_round = list(score)

            async def _grade(
                prompt: list[dict[str, str]],
                *,
                weight: float,
                round_n: int,
                obs_context: Any,
                rubric_id: str,
                rubric_version: int,
                cache_hit: bool = False,
            ) -> JudgeOpinion:
                idx = max(0, round_n - 1)
                round_score = scores_per_round[min(idx, len(scores_per_round) - 1)]
                return _make_opinion(
                    judge_id=judge_id,
                    score=round_score,
                    weight=weight,
                    round_n=round_n,
                    reasoning=reasoning,
                    confidence=confidence,
                    cost_usd=cost_usd,
                    latency_ms=latency_ms,
                    cache_hit=cache_hit,
                    injection_attempt_detected=injection_attempt_detected,
                )

            adapter.grade = _grade
        else:
            single_score = score

            async def _grade_single(
                prompt: list[dict[str, str]],
                *,
                weight: float,
                round_n: int,
                obs_context: Any,
                rubric_id: str,
                rubric_version: int,
                cache_hit: bool = False,
            ) -> JudgeOpinion:
                return _make_opinion(
                    judge_id=judge_id,
                    score=single_score,
                    weight=weight,
                    round_n=round_n,
                    reasoning=reasoning,
                    confidence=confidence,
                    cost_usd=cost_usd,
                    latency_ms=latency_ms,
                    cache_hit=cache_hit,
                    injection_attempt_detected=injection_attempt_detected,
                )

            adapter.grade = _grade_single

        return adapter

    return _build


# ════════════════════════════════════════════════════════════════════════
# grader_session — stub AsyncSession (no real DB)
# ════════════════════════════════════════════════════════════════════════


@pytest.fixture
def grader_session() -> Any:
    """Stub ``AsyncSession`` — exposes ``execute`` as ``AsyncMock``.

    Cache lookup paths return scalar_one_or_none → None (cache MISS).
    Persist paths execute without raising (no-op). Tests that need a
    HIT customize the mock per-test.
    """
    session = MagicMock()
    session.execute = AsyncMock()
    miss_result = MagicMock()
    miss_result.scalar_one_or_none = MagicMock(return_value=None)
    session.execute.return_value = miss_result
    return session


# ════════════════════════════════════════════════════════════════════════
# Helpers — duck-typed Story D goldens shape
# ════════════════════════════════════════════════════════════════════════


class _FakeTurn:
    """Duck-typed Story D ``GoldenTurnModel`` surrogate for unit tests.

    Production scenarios (``@pytest.mark.eval``, ``--run-evals``) consume
    the real ``GoldenScenarioModel`` loaded from
    ``backend/tests/agentic_evals/sales_agent/goldens/``.
    """

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

    def model_copy(self, *, update: dict[str, Any]) -> "_FakeTurn":
        return _FakeTurn(
            role=self.role,
            turn_number=self.turn_number,
            content=update.get("content", self.content),
            tool_calls=self.tool_calls,
        )


class _FakeVoiceProfile:
    """Duck-typed Story A ``PersonalityProfile`` surrogate for unit tests."""

    def __init__(
        self,
        *,
        system_instruction: str = "ASI HABLAS: warm + brief; ASI NO: aloof",
        dialect_code: str = "es-419",
    ) -> None:
        self.system_instruction = system_instruction
        self.dialect_code = dialect_code


def _build_obs_context_stub(simulation_id: str | None = None) -> Any:
    """Stub :class:`EvalSimulatorObservabilityContext`.

    Exposes ``eval_metadata`` (dict) and ``langchain_config`` (callable
    returning a dict) — the two surfaces consumed by ``_JudgeAdapter.grade``.
    """
    obs = MagicMock()
    obs.eval_metadata = {
        "eval_run_kind": "simulator",
        "archetype_slug": "tenant_coach_lat",
        "actor_profile_id": "actor_happy_001",
        "trial_n": 0,
        "simulation_id": simulation_id or "sim-stub",
        "run_id": "run-stub",
    }
    obs.langchain_config = MagicMock(return_value={"metadata": {}})
    return obs


def _utc_now() -> datetime:
    """UTC tz-aware now (mirror of shared/domain/datetime_utils.utc_now)."""
    return datetime.now(tz=timezone.utc)


__all__ = [
    "JUDGE_MODELS_LOOKUP",
    "_FakeTurn",
    "_FakeVoiceProfile",
    "_build_obs_context_stub",
    "_make_opinion",
    "_utc_now",
    "grader_session",
    "mock_judge_factory",
]
