"""Validator-path canonical cache tests (Story E T-9).

The 04-validators.yaml validators reference this exact path with free-function
test names. Tests delegate to the comprehensive class-based test suite in
``test_cache_unit.py`` plus new integration tests for Scenario 3 cache hit
end-to-end deterministic behavior.

Validators wired:
  - scenario_3_cache_hit_deterministic → test_cache_hit_deterministic
  - cache_invalidation_precision → test_cache_invalidates_on_*
  - agentic_judge_set_hash_invalidation → test_judge_set_hash_invalidation

# voseo-allowed: docstring quotes validator path naming
"""

# NO ``from __future__ import annotations`` — story-wide cement parity.

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.agentic_evals.sales_agent.grader._internal.cache import (
    cache_lookup,
    cache_persist,
    compute_cache_key,
    compute_judge_set_hash,
    compute_tenant_voice_hash,
    compute_transcript_hash,
)
from tests.agentic_evals.sales_agent.grader.conftest import _FakeTurn, _FakeVoiceProfile
from tests.agentic_evals.sales_agent.grader.result import (
    JudgeOpinion,
    MajEvalScore,
)
from tests.agentic_evals.sales_agent.grader.scenarios.test_scenario_3_cache_idempotency import (
    test_cache_hit_deterministic,
)

pytestmark = pytest.mark.no_eval


# ════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════


def _baseline_inputs() -> dict[str, Any]:
    """Default 5-field hash input set for compute_cache_key."""
    return {
        "judge_set_hash": "a" * 64,
        "rubric_id": "voice-fidelity",
        "rubric_version": 1,
        "tenant_voice_hash": "b" * 64,
        "transcript_hash": "c" * 64,
    }


def _make_score(simulation_id: str = "sim-cache-test") -> MajEvalScore:
    """Construct a deterministic ``MajEvalScore`` for cache persist tests."""
    judges = [
        JudgeOpinion(
            judge_id="sonnet",  # type: ignore[arg-type]
            model_used="claude-sonnet-4-6",
            weight=0.4,
            score=0.85,
            reasoning="ok",
            confidence=0.9,
            latency_ms=100,
            tokens_input=50,
            tokens_output=30,
            cost_usd=0,  # type: ignore[arg-type]
            round_n=1,
            cache_hit=False,
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
        actor_profile_id="actor_001",
        judges=judges,
        round_1_score=0.85,
        round_2_score=None,
        final_score=0.85,
        round_1_variance=0.0,
        round_2_variance=None,
        debate_triggered=False,
        unconverged=False,
        r2_partial=False,
        suspicious=False,
        injection_attempt_detected=False,
        cost_usd_total=0,  # type: ignore[arg-type]
        latency_ms_total=100,
        cache_hit_count=0,
        created_at=datetime.now(tz=timezone.utc),
    )


# ════════════════════════════════════════════════════════════════════════
# Hash composition tests (validator: be_lint, be_format, scenario_3)
# ════════════════════════════════════════════════════════════════════════


def test_compute_cache_key_deterministic() -> None:
    """Same 5-field inputs → same 64-char sha256 hex (D8 cement)."""
    key_a = compute_cache_key(**_baseline_inputs())
    key_b = compute_cache_key(**_baseline_inputs())
    assert key_a == key_b
    assert len(key_a) == 64
    assert all(c in "0123456789abcdef" for c in key_a)


# ════════════════════════════════════════════════════════════════════════
# Cache invalidation precision tests (validator: cache_invalidation_precision)
# ════════════════════════════════════════════════════════════════════════


def test_cache_invalidates_on_judge_weight_change() -> None:
    """Bumping JUDGE_WEIGHTS dict → judge_set_hash changes → cache key changes (D16)."""
    baseline = {"sonnet": 0.4, "gpt4o": 0.4, "kimi": 0.2}
    tuned = {"sonnet": 0.5, "gpt4o": 0.3, "kimi": 0.2}
    assert compute_judge_set_hash(baseline) != compute_judge_set_hash(tuned)

    inputs_baseline = _baseline_inputs()
    inputs_baseline["judge_set_hash"] = compute_judge_set_hash(baseline)
    inputs_tuned = _baseline_inputs()
    inputs_tuned["judge_set_hash"] = compute_judge_set_hash(tuned)
    assert compute_cache_key(**inputs_baseline) != compute_cache_key(**inputs_tuned)


def test_cache_invalidates_on_rubric_version_bump() -> None:
    """Rubric version bump → cache key changes (D16 cement)."""
    inputs_v1 = _baseline_inputs()
    inputs_v1["rubric_version"] = 1
    inputs_v2 = _baseline_inputs()
    inputs_v2["rubric_version"] = 2
    assert compute_cache_key(**inputs_v1) != compute_cache_key(**inputs_v2)


def test_cache_invalidates_on_voice_change() -> None:
    """Editing personality_profile.system_instruction → tenant_voice_hash changes."""
    voice_a = _FakeVoiceProfile(system_instruction="Tono cálido y cercano.")
    voice_b = _FakeVoiceProfile(system_instruction="Tono formal y técnico.")
    hash_a = compute_tenant_voice_hash(voice_a)
    hash_b = compute_tenant_voice_hash(voice_b)
    assert hash_a != hash_b

    inputs_a = _baseline_inputs()
    inputs_a["tenant_voice_hash"] = hash_a
    inputs_b = _baseline_inputs()
    inputs_b["tenant_voice_hash"] = hash_b
    assert compute_cache_key(**inputs_a) != compute_cache_key(**inputs_b)


def test_cache_invalidates_on_transcript_change() -> None:
    """Transcript byte change → transcript_hash changes → cache key changes."""
    baseline = [
        _FakeTurn(role="customer", turn_number=0, content="hola"),
        _FakeTurn(role="agent", turn_number=1, content="bienvenido"),
    ]
    mutated = [
        _FakeTurn(role="customer", turn_number=0, content="hola"),
        _FakeTurn(role="agent", turn_number=1, content="MUTATED"),
    ]
    hash_baseline = compute_transcript_hash(baseline)
    hash_mutated = compute_transcript_hash(mutated)
    assert hash_baseline != hash_mutated


def test_judge_set_hash_invalidation() -> None:
    """Bumping any judge weight → judge_set_hash changes → cache miss → re-grade.

    Validator-path required by ``agentic_judge_set_hash_invalidation``.
    """
    weights_v1 = {"sonnet": 0.4, "gpt4o": 0.4, "kimi": 0.2}
    weights_v2 = {"sonnet": 0.45, "gpt4o": 0.40, "kimi": 0.15}
    weights_v3 = {"sonnet": 0.4, "gpt4o": 0.4, "kimi": 0.2}  # equal v1
    h1 = compute_judge_set_hash(weights_v1)
    h2 = compute_judge_set_hash(weights_v2)
    h3 = compute_judge_set_hash(weights_v3)
    assert h1 != h2, "Weight tune must change judge_set_hash"
    assert h1 == h3, "Same weights must produce same hash (deterministic)"


# ════════════════════════════════════════════════════════════════════════
# Cache lookup / persist with graceful degradation (Rule 2)
# ════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_cache_db_unavailable_graceful() -> None:
    """DB connection error during cache_lookup → return None + log warn (Rule 2)."""
    from sqlalchemy.exc import OperationalError

    session = MagicMock()
    session.execute = AsyncMock(
        side_effect=OperationalError("SELECT 1", {}, BaseException("connection refused")),
    )

    # Must NOT raise.
    result = await cache_lookup(session, "z" * 64)
    assert result is None


@pytest.mark.asyncio
async def test_cache_persist_idempotent_on_conflict_do_nothing() -> None:
    """ON CONFLICT DO NOTHING — second persist with same key is no-op."""
    score = _make_score()
    session = MagicMock()
    session.execute = AsyncMock()

    await cache_persist(
        session=session,
        cache_key="d" * 64,
        score=score,
        transcript_hash="a" * 64,
        rubric_id="voice-fidelity",
        rubric_version=1,
        tenant_voice_hash="b" * 64,
        judge_set_hash="c" * 64,
    )

    session.execute.assert_awaited_once()
    call_args = session.execute.call_args
    stmt = call_args[0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": False}))
    assert "ON CONFLICT" in compiled.upper()
    assert "DO NOTHING" in compiled.upper()


__all__ = [
    "test_cache_db_unavailable_graceful",
    "test_cache_hit_deterministic",
    "test_cache_invalidates_on_judge_weight_change",
    "test_cache_invalidates_on_rubric_version_bump",
    "test_cache_invalidates_on_transcript_change",
    "test_cache_invalidates_on_voice_change",
    "test_cache_persist_idempotent_on_conflict_do_nothing",
    "test_compute_cache_key_deterministic",
    "test_judge_set_hash_invalidation",
]
