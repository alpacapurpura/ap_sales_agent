"""Unit tests for cache.py — hash composition + lookup/persist + graceful degradation (T-6 TDD).

D8 cement: cache key composition order FROZEN (5 fields alphabetical).
D16 cement: rubric_version bump → cache automatic invalidation.
Graceful Degradation Rule 2: DB unavailable → log warn + return None / skip persist.

Tests:
- test_cache_key_deterministic_same_request_same_key
- test_cache_key_changes_on_transcript_mutation
- test_cache_key_changes_on_rubric_version_bump (D8/D16 — cement)
- test_cache_key_changes_on_voice_profile_change
- test_cache_key_changes_on_judge_set_change
- test_lookup_returns_none_on_cache_miss
- test_lookup_returns_score_on_cache_hit_with_hit_count_increment
- test_persist_idempotent_first_writer_wins
- test_lookup_graceful_db_unavailable_returns_none

Pure unit tests — no LLM, no real DB. Marked @pytest.mark.no_eval — run on default CI.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import OperationalError

from tests.agentic_evals.sales_agent.grader._internal.cache import (
    _CACHE_KEY_FIELDS,
    cache_lookup,
    cache_persist,
    compute_cache_key,
    compute_judge_set_hash,
    compute_tenant_voice_hash,
    compute_transcript_hash,
)
from tests.agentic_evals.sales_agent.grader.result import (
    JudgeOpinion,
    MajEvalScore,
)

pytestmark = pytest.mark.no_eval  # Pure unit tests — no LLM, mocked DB


# ──────────────────────────────────────────────────────────────────────────────
# Test helpers — minimal stand-ins for Story C/D types
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _StubTurn:
    """Minimal duck-typed stand-in for Story D GoldenTurnModel.

    cache.py treats the transcript items duck-typed (Pydantic Any in
    RubricGradeRequest avoids circular imports). Tests verify hashing reads
    role + turn_number + content from each item.
    """

    role: str
    turn_number: int
    content: str


class _StubVoiceProfile(BaseModel):
    """Minimal duck-typed stand-in for Story A PersonalityProfile.

    cache.py reads voice_profile.system_instruction verbatim per
    sales-agent-expert §3 SSoT cement.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    system_instruction: str


def _make_score(**overrides: object) -> MajEvalScore:
    """Build a minimal valid MajEvalScore for cache roundtrip."""
    judges = [
        JudgeOpinion(
            judge_id="sonnet",
            model_used="claude-sonnet-4-6",
            weight=0.4,
            score=0.85,
            reasoning="Voice fidelity high.",
            confidence=0.9,
            latency_ms=1200,
            tokens_input=500,
            tokens_output=120,
            cost_usd=Decimal("0.003"),
            round_n=1,
            cache_hit=False,
        ),
        JudgeOpinion(
            judge_id="gpt4o",
            model_used="gpt-4o-2024-11-20",
            weight=0.4,
            score=0.80,
            reasoning="Reasonable warmth.",
            confidence=0.88,
            latency_ms=1100,
            tokens_input=500,
            tokens_output=110,
            cost_usd=Decimal("0.002"),
            round_n=1,
            cache_hit=False,
        ),
        JudgeOpinion(
            judge_id="kimi",
            model_used="kimi-k2.6",
            weight=0.2,
            score=0.78,
            reasoning="Slightly stiff.",
            confidence=0.85,
            latency_ms=900,
            tokens_input=500,
            tokens_output=105,
            cost_usd=Decimal("0.001"),
            round_n=1,
            cache_hit=False,
        ),
    ]
    defaults: dict[str, Any] = {
        "simulation_id": "11111111-1111-1111-1111-111111111111",
        "turn_n": 1,
        "rubric_id": "voice-fidelity",
        "rubric_version": 1,
        "tenant_slug": "tenant_coach_lat",
        "persona_kind": "happy",
        "actor_profile_id": "coach_lat_happy_v1",
        "judges": judges,
        "round_1_score": 0.82,
        "final_score": 0.82,
        "round_1_variance": 0.07,
        "latency_ms_total": 3200,
        "cache_hit_count": 0,
        "created_at": datetime(2026, 5, 9, 0, 0, 0, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    return MajEvalScore(**defaults)


def _hash_inputs(**overrides: Any) -> dict[str, Any]:
    """Default kwargs for compute_cache_key."""
    defaults: dict[str, Any] = {
        "transcript_hash": "a" * 64,
        "rubric_id": "voice-fidelity",
        "rubric_version": 1,
        "tenant_voice_hash": "b" * 64,
        "judge_set_hash": "c" * 64,
    }
    defaults.update(overrides)
    return defaults


# ──────────────────────────────────────────────────────────────────────────────
# Tests — composition (D8/D16 cement)
# ──────────────────────────────────────────────────────────────────────────────


class TestCacheKeyDeterministicSameRequestSameKey:
    """Same inputs MUST produce same 64-char sha256 hex (D8 cement)."""

    def test_same_inputs_same_key(self) -> None:
        """Idempotent composition — same 5 fields → same hex."""
        key_a = compute_cache_key(**_hash_inputs())
        key_b = compute_cache_key(**_hash_inputs())
        assert key_a == key_b

    def test_key_is_64_char_hex(self) -> None:
        """Cache PK = VARCHAR(64). Length cement."""
        key = compute_cache_key(**_hash_inputs())
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

    def test_cache_key_fields_frozen_alphabetical_order(self) -> None:
        """Composition order MUST be alphabetical — D8 cement.

        Drift in this order silently breaks idempotency across deploys.
        """
        assert _CACHE_KEY_FIELDS == (
            "judge_set_hash",
            "rubric_id",
            "rubric_version",
            "tenant_voice_hash",
            "transcript_hash",
        )


class TestCacheKeyChangesOnTranscriptMutation:
    """Transcript byte change → transcript_hash change → key change → cache miss."""

    def test_transcript_hash_change_invalidates_key(self) -> None:
        """Byte mutation in transcript_hash → composition key changes."""
        key_a = compute_cache_key(**_hash_inputs(transcript_hash="a" * 64))
        key_b = compute_cache_key(**_hash_inputs(transcript_hash="d" * 64))
        assert key_a != key_b

    def test_compute_transcript_hash_changes_on_content_edit(self) -> None:
        """Real transcript[].content edit → upstream hash changes → cache miss."""
        baseline = [
            _StubTurn(role="customer", turn_number=0, content="hola, ¿qué tal?"),
            _StubTurn(role="agent", turn_number=1, content="bien, ¿en qué te ayudo?"),
        ]
        mutated = [
            _StubTurn(role="customer", turn_number=0, content="hola, ¿qué tal?"),
            _StubTurn(role="agent", turn_number=1, content="MUTATED RESPONSE"),
        ]
        assert compute_transcript_hash(baseline) != compute_transcript_hash(mutated)

    def test_compute_transcript_hash_deterministic(self) -> None:
        """Same transcript → same hash (Story B byte-equal determinism cement)."""
        transcript = [
            _StubTurn(role="customer", turn_number=0, content="hola"),
            _StubTurn(role="agent", turn_number=1, content="hola, bienvenido"),
        ]
        assert compute_transcript_hash(transcript) == compute_transcript_hash(transcript)


class TestCacheKeyChangesOnRubricVersionBump:
    """D8/D16 cement — rubric_version bump → automatic cache invalidation."""

    def test_rubric_version_bump_invalidates_key(self) -> None:
        """v1 vs v2 of rubric → different cache keys → forced re-grade.

        This is the D16 cement: rubric MD edit bumps version → automatic
        invalidation across all cached entries for that rubric.
        """
        key_v1 = compute_cache_key(**_hash_inputs(rubric_version=1))
        key_v2 = compute_cache_key(**_hash_inputs(rubric_version=2))
        assert key_v1 != key_v2

    def test_rubric_id_change_invalidates_key(self) -> None:
        """Different rubric_id → different cache key (4 rubrics in scope)."""
        key_voice = compute_cache_key(**_hash_inputs(rubric_id="voice-fidelity"))
        key_qual = compute_cache_key(**_hash_inputs(rubric_id="qualification-accuracy"))
        assert key_voice != key_qual


class TestCacheKeyChangesOnVoiceProfileChange:
    """Voice edit → tenant_voice_hash change → key change."""

    def test_voice_hash_change_invalidates_key(self) -> None:
        """Different tenant_voice_hash → different cache key."""
        key_a = compute_cache_key(**_hash_inputs(tenant_voice_hash="b" * 64))
        key_b = compute_cache_key(**_hash_inputs(tenant_voice_hash="e" * 64))
        assert key_a != key_b

    def test_compute_tenant_voice_hash_reads_system_instruction_verbatim(self) -> None:
        """voice_profile.system_instruction is SSoT (sales-agent-expert §3 cement)."""
        v1 = _StubVoiceProfile(system_instruction="Tono cálido y cercano.")
        v2 = _StubVoiceProfile(system_instruction="Tono formal y técnico.")
        assert compute_tenant_voice_hash(v1) != compute_tenant_voice_hash(v2)

    def test_compute_tenant_voice_hash_deterministic(self) -> None:
        """Same system_instruction → same hash."""
        v1 = _StubVoiceProfile(system_instruction="Igual contenido.")
        v2 = _StubVoiceProfile(system_instruction="Igual contenido.")
        assert compute_tenant_voice_hash(v1) == compute_tenant_voice_hash(v2)


class TestCacheKeyChangesOnJudgeSetChange:
    """Judge weight tuning → judge_set_hash change → key change (D2 cement)."""

    def test_judge_set_hash_change_invalidates_key(self) -> None:
        """Different judge_set_hash → different cache key."""
        key_a = compute_cache_key(**_hash_inputs(judge_set_hash="c" * 64))
        key_b = compute_cache_key(**_hash_inputs(judge_set_hash="f" * 64))
        assert key_a != key_b

    def test_compute_judge_set_hash_changes_on_weight_tune(self) -> None:
        """Bump Sonnet 0.4 → 0.5 → judge_set_hash changes → cache invalidates."""
        baseline = {"sonnet": 0.4, "gpt4o": 0.4, "kimi": 0.2}
        tuned = {"sonnet": 0.5, "gpt4o": 0.3, "kimi": 0.2}
        assert compute_judge_set_hash(baseline) != compute_judge_set_hash(tuned)

    def test_compute_judge_set_hash_canonical_order(self) -> None:
        """Insertion order MUST NOT matter (sort_keys=True cement)."""
        order_a = {"sonnet": 0.4, "gpt4o": 0.4, "kimi": 0.2}
        order_b = {"kimi": 0.2, "sonnet": 0.4, "gpt4o": 0.4}
        assert compute_judge_set_hash(order_a) == compute_judge_set_hash(order_b)


# ──────────────────────────────────────────────────────────────────────────────
# Tests — cache_lookup
# ──────────────────────────────────────────────────────────────────────────────


class TestLookupReturnsNoneOnCacheMiss:
    """Cache miss → return None (no exception)."""

    async def test_lookup_returns_none_when_no_row(self) -> None:
        """Empty result set → None."""
        session = MagicMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        result = await cache_lookup(session, "nonexistent_key" + "0" * 48)

        assert result is None
        session.execute.assert_awaited_once()


class TestLookupReturnsScoreOnCacheHitWithHitCountIncrement:
    """Cache hit → reconstruct MajEvalScore + update last_hit_at."""

    async def test_lookup_returns_majeval_on_hit_and_updates_last_hit_at(self) -> None:
        """On hit: reconstruct MajEvalScore from JSONB payload + UPDATE last_hit_at."""
        original = _make_score()

        # Mock the cache row
        cached_row = MagicMock()
        cached_row.payload = original.model_dump(mode="json")
        cached_row.cache_key = "x" * 64

        select_result = MagicMock()
        select_result.scalar_one_or_none.return_value = cached_row

        session = MagicMock()
        session.execute = AsyncMock(return_value=select_result)
        session.commit = AsyncMock()

        result = await cache_lookup(session, "x" * 64)

        assert result is not None
        assert isinstance(result, MajEvalScore)
        # Roundtrip preserves cement fields
        assert result.simulation_id == original.simulation_id
        assert result.rubric_id == original.rubric_id
        assert result.final_score == original.final_score
        # Two execute calls: SELECT + UPDATE last_hit_at
        assert session.execute.await_count == 2


# ──────────────────────────────────────────────────────────────────────────────
# Tests — cache_persist
# ──────────────────────────────────────────────────────────────────────────────


class TestPersistIdempotentFirstWriterWins:
    """ON CONFLICT DO NOTHING — idempotent first-writer-wins (D-BE-2 / D8)."""

    async def test_persist_uses_on_conflict_do_nothing(self) -> None:
        """Second persist with same key → no exception, payload not overwritten.

        Verified via SQL statement string contains ON CONFLICT DO NOTHING.
        """
        score = _make_score()
        session = MagicMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()

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

        # Persist invoked
        session.execute.assert_awaited_once()
        # Verify the bound statement uses ON CONFLICT DO NOTHING (idempotent)
        call_args = session.execute.call_args
        stmt = call_args[0][0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": False}))
        assert "ON CONFLICT" in compiled.upper()
        assert "DO NOTHING" in compiled.upper()


# ──────────────────────────────────────────────────────────────────────────────
# Tests — graceful degradation Rule 2
# ──────────────────────────────────────────────────────────────────────────────


class TestLookupGracefulDbUnavailableReturnsNone:
    """DB unavailable → log warn + return None (NOT raise) per Rule 2 cement."""

    async def test_lookup_returns_none_when_db_raises(self) -> None:
        """OperationalError → caught + structlog warn + return None."""
        session = MagicMock()
        session.execute = AsyncMock(
            side_effect=OperationalError("SELECT 1", {}, BaseException("connection refused")),
        )

        # Must NOT raise
        result = await cache_lookup(session, "z" * 64)
        assert result is None

    async def test_persist_does_not_raise_when_db_raises(self) -> None:
        """Persist failure → caught + structlog warn + skip (not raise)."""
        score = _make_score()
        session = MagicMock()
        session.execute = AsyncMock(
            side_effect=OperationalError("INSERT", {}, BaseException("connection refused")),
        )
        session.commit = AsyncMock()

        # Must NOT raise
        await cache_persist(
            session=session,
            cache_key="g" * 64,
            score=score,
            transcript_hash="a" * 64,
            rubric_id="voice-fidelity",
            rubric_version=1,
            tenant_voice_hash="b" * 64,
            judge_set_hash="c" * 64,
        )
