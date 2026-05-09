"""MAJ-EVAL state machine — Round 1 + variance check + Round 2 + persist (Story E T-5).

Reference impl: ``docs/product/stories/sales-agent-voice-fidelity-grader-runtime/03-arch.md§4.3``.

State machine
=============

Per (turn x rubric):

1. **Cache lookup** — compute deterministic 5-field key (D8 cement). HIT → return
   cached :class:`MajEvalScore`. MISS → continue to Round 1.
2. **Round 1** — 3 judges in parallel via ``asyncio.gather`` with
   ``Semaphore(JUDGE_CONCURRENCY=20)`` (D17 cement, provider DoS protection).
3. **Variance check** — ``max(scores) - min(scores)`` simple range (D3 spec —
   NOT statistical variance). Threshold ``VARIANCE_R1_THRESHOLD=0.15``.
4. **Branch**:
   * variance ≤ 0.15 → ``debate_triggered=False``; aggregate Round 1 weighted avg.
   * variance > 0.15 → trigger Round 2.
5. **Round 2** (debate, conditional) — each judge sees ONLY OTHER 2 peers' R1
   reasoning (DQ3 anti-anchoring cement — NEVER own).
6. **Convergence** — ``VARIANCE_R2_TARGET=0.10`` (D4 cement):
   * R2 variance < 0.10 → ``unconverged=False``; ``final_score = R2 weighted avg``.
   * R2 variance ≥ 0.10 → ``unconverged=True`` + ``final_score = R1 weighted avg``
     fallback + structlog warn (DQ8 cement: NOT block — graceful degradation).
7. **R2 partial fallback** (DQ6) — judge fails R2 (score=None) → use that judge's
   R1 score for variance + weighted avg + flag ``r2_partial=True``.
8. **Suspicious flag** (DQ8) — all 3 judges score=1.0 + ANY ``injection_attempt_detected``
   → ``suspicious=True`` + structlog warn (audit trail for adversarial scenarios).
9. **<2 valid judges defense** — if fewer than 2 judges return valid scores
   (rare degenerate case) → ``unconverged=True``, structlog error.
10. **Persist + cache** — best-effort try/except (graceful degradation Rule 2).
    DB unavailable → log warn + skip; the in-memory result list still returns.

Cement decisions
================

* **D3** — variance threshold 0.15 (max-min, NOT statistical).
* **D4** — unconverged fallback to R1 weighted avg.
* **D17** — Semaphore(20) concurrency cap.
* **D-AG-3** — asyncio.gather Round 1 parallel.
* **D-AG-4** — Round 2 conditional (only on variance > 0.15).
* **D-AG-5** — Peer-only reasoning (anti-anchoring DQ3).
* **D-AG-6** — Judge timeout fallback (DQ6 r2_partial).
* **D-AG-9** — Judge concurrency Semaphore(20).
* **D-AG-10** — DB write best-effort (Graceful Degradation Rule 2).
* **D-AG-12** — State machine cement (this module).
* **D10** — PII sanitize defense-in-depth pre-judge.

# voseo-allowed: docstring cita rubric IDs canónicos en spec v2 + D-AG cement
"""

# NOTE: NO ``from __future__ import annotations`` — Pydantic Literal runtime
# introspection (Story B cement T-4 pattern preserved in case the grader is ever
# wired into the LangGraph compose path of run_simulation, which Story I will do).
# Story B note from arch doc §4.3 lines 836-839: keep grader compatible with
# graph compose via NO future annotations import.

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import structlog
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_simulator_grade import (
    EvalSimulatorGradeModel,
)
from src.shared.agent_observability.recording.sanitization import sanitize_payload
from tests.agentic_evals.sales_agent.grader._internal.cache import (
    cache_lookup,
    cache_persist,
    compute_cache_key,
    compute_judge_set_hash,
    compute_tenant_voice_hash,
    compute_transcript_hash,
)
from tests.agentic_evals.sales_agent.grader._internal.judge_prompts import build_judge_prompt
from tests.agentic_evals.sales_agent.grader._internal.judge_registry import (
    JUDGE_WEIGHTS,
    get_judge,
)
from tests.agentic_evals.sales_agent.grader.result import (
    JudgeOpinion,
    MajEvalScore,
    RubricGradeRequest,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from tests.agentic_evals.sales_agent.simulator._internal.observability import (
        EvalSimulatorObservabilityContext,
    )

logger = structlog.get_logger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Cement constants — Final to enforce module-level immutability.
# ──────────────────────────────────────────────────────────────────────────────


VARIANCE_R1_THRESHOLD: Final[float] = 0.15
"""D3 cement — Round 2 trigger threshold (max - min over R1 scores)."""

VARIANCE_R2_TARGET: Final[float] = 0.10
"""D4 cement — R2 convergence target. R2 variance ≥ this → unconverged + R1 fallback."""

JUDGE_CONCURRENCY: Final[int] = 20
"""D17 cement — Semaphore cap on concurrent judge LLM dispatches (provider DoS protection)."""


# Resolve rubrics directory once — process-scoped lookup.
# ``backend/tests/agentic_evals/sales_agent/grader/_internal/maj_eval.py``:
# parents[0]=_internal, [1]=grader, [2]=sales_agent, [3]=agentic_evals,
# [4]=tests, [5]=backend, [6]=repo root → ``docs/specs/rubrics/``.
_RUBRICS_DIR: Final[Path] = Path(__file__).resolve().parents[6] / "docs" / "specs" / "rubrics"


# ──────────────────────────────────────────────────────────────────────────────
# Public entry point — grade_transcript_maj_eval
# ──────────────────────────────────────────────────────────────────────────────


async def grade_transcript_maj_eval(
    request: RubricGradeRequest,
    *,
    session: "AsyncSession",
    obs_context: "EvalSimulatorObservabilityContext",
) -> list[MajEvalScore]:
    """MAJ-EVAL grader — Round 1 parallel + Round 2 conditional + cache + persist.

    Public API (Story E H9 expand 7→8 — exposed via ``simulator/__init__.py`` T-8).
    Returns a list of :class:`MajEvalScore`, one per ``(turn x rubric)`` pair.

    Workflow per (turn, rubric):

    1. PII-sanitize transcript turn (D10 — defense-in-depth).
    2. Compute cache key (5-field deterministic sha256, D8 cement).
    3. Cache lookup — HIT → reuse cached :class:`MajEvalScore`; MISS → continue.
    4. Round 1: 3 judges in parallel via :func:`asyncio.gather` + Semaphore(20).
    5. Variance check (max-min; D3): trigger Round 2 if > 0.15.
    6. Round 2 (conditional): peer-only reasoning (DQ3); each judge sees the
       OTHER 2 peers' R1 reasoning, NEVER their own.
    7. Convergence: R2 variance < 0.10 → final_score = R2; else unconverged + R1 fallback.
    8. Persist :class:`MajEvalScore` + cache (best-effort try/except Rule 2).

    Parameters
    ----------
    request:
        Frozen :class:`RubricGradeRequest` with transcript, voice profile,
        rubrics list, simulation context.
    session:
        SQLAlchemy 2.0 async session for grade + cache writes.
    obs_context:
        Story B :class:`EvalSimulatorObservabilityContext` — passed into judge
        adapters so cost / observability rows fire under the eval cost bucket
        (H7 cement).

    Returns
    -------
    list[MajEvalScore]:
        One row per ``(turn x rubric)`` — frozen Pydantic v2 model instances.
    """
    # PII sanitize defense-in-depth (D10) — defensive even with synthetic data.
    # ``sanitize_payload`` accepts dict[str, Any]; we wrap each turn's content
    # in a single-key dict and unwrap. The sanitized turn replaces the original
    # via Pydantic-style ``model_copy`` (duck-typed for forward compatibility
    # with both real Story D ``GoldenTurnModel`` and unit-test stubs).
    sanitized: list[Any] = []
    for turn in request.transcript:
        try:
            sanitized_dict = sanitize_payload({"content": turn.content})
            sanitized_content = sanitized_dict.get("content", turn.content)
        except Exception as exc:  # noqa: BLE001 — sanitize fail = passthrough (best-effort)
            logger.warning(
                "grader_pii_sanitize_failed",
                turn_number=getattr(turn, "turn_number", None),
                error=str(exc),
                fallback="passthrough",
            )
            sanitized_content = turn.content
        sanitized.append(turn.model_copy(update={"content": sanitized_content}))

    # Pre-compute hashes (idempotent, deterministic).
    transcript_hash = compute_transcript_hash(sanitized)
    tenant_voice_hash = compute_tenant_voice_hash(request.tenant_voice_profile)
    judge_set_hash = compute_judge_set_hash(JUDGE_WEIGHTS)

    results: list[MajEvalScore] = []

    # Iterate (turn, rubric). Sequential cross-turn (cache may short-circuit), but
    # async per-turn (3 judges parallel within a turn x rubric).
    total_turns = len(sanitized)
    for turn_n in range(1, total_turns + 1):
        turn = sanitized[turn_n - 1]
        for rubric_id in request.rubrics:
            rubric_version = _get_rubric_version(rubric_id)
            cache_key = compute_cache_key(
                transcript_hash=transcript_hash,
                rubric_id=rubric_id,
                rubric_version=rubric_version,
                tenant_voice_hash=tenant_voice_hash,
                judge_set_hash=judge_set_hash,
            )

            # Cache lookup — graceful if DB unavailable (Rule 2).
            cached: MajEvalScore | None = None
            if request.cache_policy == "use":
                try:
                    cached = await cache_lookup(session, cache_key)
                except Exception as exc:  # noqa: BLE001 — Rule 2 graceful degradation
                    logger.warning(
                        "grader_cache_lookup_failed",
                        cache_key_prefix=cache_key[:16],
                        rubric_id=rubric_id,
                        error=str(exc),
                        fallback="re-grade",
                    )
                    cached = None

            if cached is not None:
                results.append(cached)
                continue

            # MISS → grade Round 1 + (conditional) Round 2.
            score = await _grade_one_turn_rubric(
                turn=turn,
                request=request,
                turn_n=turn_n,
                rubric_id=rubric_id,
                rubric_version=rubric_version,
                obs_context=obs_context,
            )

            # Persist + cache — best-effort (Rule 2). NEVER raise out.
            try:
                await _persist_grade(session, score)
            except Exception as exc:  # noqa: BLE001 — Rule 2 graceful degradation
                logger.warning(
                    "grader_persist_grade_failed",
                    simulation_id=score.simulation_id,
                    turn_n=score.turn_n,
                    rubric_id=score.rubric_id,
                    error=str(exc),
                    fallback="skip-persist",
                )

            try:
                await cache_persist(
                    session=session,
                    cache_key=cache_key,
                    score=score,
                    transcript_hash=transcript_hash,
                    rubric_id=rubric_id,
                    rubric_version=rubric_version,
                    tenant_voice_hash=tenant_voice_hash,
                    judge_set_hash=judge_set_hash,
                )
            except Exception as exc:  # noqa: BLE001 — Rule 2 graceful degradation
                logger.warning(
                    "grader_cache_persist_failed",
                    cache_key_prefix=cache_key[:16],
                    rubric_id=rubric_id,
                    error=str(exc),
                    fallback="skip-cache",
                )

            results.append(score)

    return results


# ──────────────────────────────────────────────────────────────────────────────
# Per-(turn x rubric) state machine
# ──────────────────────────────────────────────────────────────────────────────


async def _grade_one_turn_rubric(
    *,
    turn: Any,
    request: RubricGradeRequest,
    turn_n: int,
    rubric_id: str,
    rubric_version: int,
    obs_context: "EvalSimulatorObservabilityContext",
) -> MajEvalScore:
    """Grade one (turn x rubric) → 1 :class:`MajEvalScore`.

    Round 1 + conditional Round 2 + variance + fallbacks per design §1.
    """
    # Round 1 — 3 judges in parallel with Semaphore concurrency cap.
    semaphore = asyncio.Semaphore(JUDGE_CONCURRENCY)
    r1_tasks = [
        _invoke_judge(
            judge_id=jid,
            weight=weight,
            request=request,
            turn_n=turn_n,
            rubric_id=rubric_id,
            rubric_version=rubric_version,
            round_n=1,
            peer_reasoning=None,
            semaphore=semaphore,
            obs_context=obs_context,
        )
        for jid, weight in JUDGE_WEIGHTS.items()
    ]
    r1_opinions = await asyncio.gather(*r1_tasks)

    # Variance check (D3) — exclude None scores.
    valid_r1 = [op for op in r1_opinions if op.score is not None]

    # <2 valid judges defense — degenerate case (rare, e.g., 2 providers down).
    if len(valid_r1) < 2:
        logger.error(
            "maj_eval_insufficient_valid_judges",
            simulation_id=request.simulation_id,
            turn_n=turn_n,
            rubric_id=rubric_id,
            valid_count=len(valid_r1),
        )
        return _build_score(
            r1_opinions=r1_opinions,
            r2_opinions=None,
            request=request,
            turn_n=turn_n,
            rubric_id=rubric_id,
            rubric_version=rubric_version,
            r1_weighted=_weighted_average(valid_r1),
            r1_variance=_variance(valid_r1),
            r2_weighted=None,
            r2_variance=None,
            debate_triggered=False,
            unconverged=True,
            r2_partial=False,
        )

    r1_weighted = _weighted_average(valid_r1)
    r1_variance = _variance(valid_r1)

    # Branch: convergence at Round 1?
    if r1_variance <= VARIANCE_R1_THRESHOLD:
        # Converged R1 — no debate.
        return _build_score(
            r1_opinions=r1_opinions,
            r2_opinions=None,
            request=request,
            turn_n=turn_n,
            rubric_id=rubric_id,
            rubric_version=rubric_version,
            r1_weighted=r1_weighted,
            r1_variance=r1_variance,
            r2_weighted=None,
            r2_variance=None,
            debate_triggered=False,
            unconverged=False,
            r2_partial=False,
        )

    # Round 2 debate — variance > 0.15.
    logger.info(
        "maj_eval_debate_triggered",
        simulation_id=request.simulation_id,
        turn_n=turn_n,
        rubric_id=rubric_id,
        variance_r1=r1_variance,
        threshold=VARIANCE_R1_THRESHOLD,
    )

    # Build peer reasoning per judge (each gets OTHER 2's R1 reasoning, NEVER own — DQ3).
    r2_tasks = []
    for jid, weight in JUDGE_WEIGHTS.items():
        peer_reasoning: list[tuple[str, float, str]] = [
            (op.judge_id, op.score, op.reasoning) for op in r1_opinions if op.judge_id != jid and op.score is not None
        ]
        r2_tasks.append(
            _invoke_judge(
                judge_id=jid,
                weight=weight,
                request=request,
                turn_n=turn_n,
                rubric_id=rubric_id,
                rubric_version=rubric_version,
                round_n=2,
                peer_reasoning=peer_reasoning,
                semaphore=semaphore,
                obs_context=obs_context,
            ),
        )
    r2_opinions = await asyncio.gather(*r2_tasks)

    # R2 partial fallback (DQ6): judge fail R2 → use R1 score for that judge.
    valid_r2 = [op for op in r2_opinions if op.score is not None]
    r2_partial = len(valid_r2) < 3

    # Build the canonical-ordered (per JUDGE_WEIGHTS) "final R2 view" — for failed
    # R2 judges, substitute R1 opinion to keep variance/avg meaningful.
    final_r2_view: list[JudgeOpinion] = []
    for jid in JUDGE_WEIGHTS:
        r2_op = next(op for op in r2_opinions if op.judge_id == jid)
        if r2_op.score is None:
            r1_op = next(op for op in r1_opinions if op.judge_id == jid)
            final_r2_view.append(r1_op)
        else:
            final_r2_view.append(r2_op)

    valid_final_r2 = [op for op in final_r2_view if op.score is not None]
    r2_weighted = _weighted_average(valid_final_r2)
    r2_variance = _variance(valid_final_r2)

    unconverged = r2_variance >= VARIANCE_R2_TARGET
    if unconverged:
        logger.warning(
            "maj_eval_unconverged",
            simulation_id=request.simulation_id,
            turn_n=turn_n,
            rubric_id=rubric_id,
            variance_r2=r2_variance,
            target=VARIANCE_R2_TARGET,
            fallback="round_1_weighted_avg",
        )

    return _build_score(
        r1_opinions=r1_opinions,
        r2_opinions=r2_opinions,
        request=request,
        turn_n=turn_n,
        rubric_id=rubric_id,
        rubric_version=rubric_version,
        r1_weighted=r1_weighted,
        r1_variance=r1_variance,
        r2_weighted=r2_weighted,
        r2_variance=r2_variance,
        debate_triggered=True,
        unconverged=unconverged,
        r2_partial=r2_partial,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Judge invocation (Semaphore + adapter dispatch)
# ──────────────────────────────────────────────────────────────────────────────


async def _invoke_judge(
    *,
    judge_id: str,
    weight: float,
    request: RubricGradeRequest,
    turn_n: int,
    rubric_id: str,
    rubric_version: int,
    round_n: int,
    peer_reasoning: list[tuple[str, float, str]] | None,
    semaphore: asyncio.Semaphore,
    obs_context: "EvalSimulatorObservabilityContext",
) -> JudgeOpinion:
    """Invoke a single judge under the Semaphore + return :class:`JudgeOpinion`.

    The judge adapter (:class:`_JudgeAdapter` from ``judge_registry``) is
    best-effort: dispatch failures + JSON parse errors return a
    :class:`JudgeOpinion` with ``score=None`` (judge fail). The aggregator
    excludes None scores from variance + weighted-average computations.
    """
    async with semaphore:
        judge = get_judge(judge_id)
        rubric_md_verbatim = _read_rubric_md(rubric_id)
        prompt = build_judge_prompt(
            request=request,
            turn_n=turn_n,
            rubric_id=rubric_id,
            rubric_version=rubric_version,
            round_n=round_n,
            peer_reasoning=peer_reasoning,
            judge_id=judge_id,
            rubric_md_verbatim=rubric_md_verbatim,
        )
        return await judge.grade(
            prompt,
            weight=weight,
            round_n=round_n,
            obs_context=obs_context,
            rubric_id=rubric_id,
            rubric_version=rubric_version,
            cache_hit=False,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Pure helpers — variance + weighted average
# ──────────────────────────────────────────────────────────────────────────────


def _weighted_average(opinions: list[JudgeOpinion]) -> float:
    """Sum(score * weight) / Sum(weight) over opinions with non-None scores.

    Renormalizes weights when a judge has score=None (failed).
    Returns 0.0 if total effective weight is zero (all judges failed).
    """
    valid = [op for op in opinions if op.score is not None]
    total_weight = sum(op.weight for op in valid)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(op.score * op.weight for op in valid if op.score is not None)
    return weighted_sum / total_weight


def _variance(opinions: list[JudgeOpinion]) -> float:
    """``max(score) - min(score)`` simple range — D3 spec NOT statistical variance.

    Returns 0.0 for empty input (all None or no opinions).
    """
    scores = [op.score for op in opinions if op.score is not None]
    if not scores:
        return 0.0
    return max(scores) - min(scores)


# ──────────────────────────────────────────────────────────────────────────────
# MajEvalScore composition
# ──────────────────────────────────────────────────────────────────────────────


def _build_score(
    *,
    r1_opinions: list[JudgeOpinion],
    r2_opinions: list[JudgeOpinion] | None,
    request: RubricGradeRequest,
    turn_n: int,
    rubric_id: str,
    rubric_version: int,
    r1_weighted: float,
    r1_variance: float,
    r2_weighted: float | None,
    r2_variance: float | None,
    debate_triggered: bool,
    unconverged: bool,
    r2_partial: bool,
) -> MajEvalScore:
    """Compose a :class:`MajEvalScore` from R1 + optional R2 opinions.

    final_score logic per spec D4:

    * Not debate triggered → ``final_score = round_1_weighted_avg``.
    * Debate + converged (R2 variance < 0.10) → ``final_score = round_2_weighted_avg``.
    * Debate + unconverged (R2 variance ≥ 0.10) → ``final_score = round_1_weighted_avg``
      (DQ8 cement: graceful degradation, NOT block).
    """
    # Build judges list — 3 (R1 only) or 6 (R1 + R2).
    judges: list[JudgeOpinion] = list(r1_opinions)
    if r2_opinions is not None:
        judges.extend(r2_opinions)

    # final_score logic per D4.
    if not debate_triggered:
        final_score = r1_weighted
    elif unconverged:
        # R2 variance ≥ 0.10 — fall back to R1 weighted avg.
        final_score = r1_weighted
    else:
        # Converged R2 — use R2 weighted avg (always available when not unconverged).
        final_score = r2_weighted if r2_weighted is not None else r1_weighted

    # Clamp final_score to [0.0, 1.0] to satisfy Pydantic Field(ge=0.0, le=1.0).
    final_score = max(0.0, min(1.0, final_score))
    r1_weighted_clamped = max(0.0, min(1.0, r1_weighted))
    r1_variance_clamped = max(0.0, min(1.0, r1_variance))
    r2_weighted_clamped = max(0.0, min(1.0, r2_weighted)) if r2_weighted is not None else None
    r2_variance_clamped = max(0.0, min(1.0, r2_variance)) if r2_variance is not None else None

    # Suspicious flag (DQ8): ALL R1 judges score=1.0 + ANY injection_attempt_detected.
    all_r1_perfect = all(op.score == 1.0 for op in r1_opinions if op.score is not None)
    has_r1_full_quorum = len([op for op in r1_opinions if op.score is not None]) == 3
    any_injection_r1 = any(op.injection_attempt_detected for op in r1_opinions)
    any_injection_r2 = any(op.injection_attempt_detected for op in (r2_opinions or []))
    any_injection = any_injection_r1 or any_injection_r2
    suspicious = bool(all_r1_perfect and has_r1_full_quorum and any_injection)
    if suspicious:
        logger.warning(
            "maj_eval_suspicious_score",
            simulation_id=request.simulation_id,
            turn_n=turn_n,
            rubric_id=rubric_id,
            reason="all_judges_score_1_with_injection_attempt",
        )

    # Cost + latency aggregation.
    cost_usd_total = sum((op.cost_usd for op in judges), Decimal(0))
    latency_ms_total = sum(op.latency_ms for op in judges)
    cache_hit_count = sum(1 for op in judges if op.cache_hit)

    return MajEvalScore(
        simulation_id=request.simulation_id,
        turn_n=turn_n,
        rubric_id=rubric_id,  # type: ignore[arg-type]
        rubric_version=rubric_version,
        tenant_slug=request.tenant_slug,
        persona_kind=request.persona_kind,
        actor_profile_id=request.actor_profile_id,
        judges=judges,
        round_1_score=r1_weighted_clamped,
        round_2_score=r2_weighted_clamped if debate_triggered else None,
        final_score=final_score,
        round_1_variance=r1_variance_clamped,
        round_2_variance=r2_variance_clamped if debate_triggered else None,
        debate_triggered=debate_triggered,
        unconverged=unconverged,
        r2_partial=r2_partial,
        suspicious=suspicious,
        injection_attempt_detected=any_injection,
        cost_usd_total=cost_usd_total,
        latency_ms_total=latency_ms_total,
        cache_hit_count=cache_hit_count,
        created_at=datetime.now(timezone.utc),
    )


# ──────────────────────────────────────────────────────────────────────────────
# Persist (best-effort) + rubric MD reader (process-scoped lru_cache)
# ──────────────────────────────────────────────────────────────────────────────


async def _persist_grade(session: "AsyncSession", score: MajEvalScore) -> None:
    """INSERT one row into ``eval_simulator_grade`` — idempotent first-writer-wins.

    Uses ``INSERT ... ON CONFLICT DO NOTHING`` on PK ``(simulation_id, turn_n,
    rubric_id)`` — concurrent runs of the same (simulation, turn, rubric) tuple
    keep the first writer's score.

    NEVER raises out — caller wraps in try/except (Rule 2). Cost-bucket invariant
    H7: judge LLM calls (counted in ``score.judges[*]``) write to
    ``eval_simulator_llm_call`` ONLY — this row aggregates grade, NOT LLM calls.
    """
    judges_payload = [op.model_dump(mode="json") for op in score.judges]
    stmt = (
        pg_insert(EvalSimulatorGradeModel)
        .values(
            schema_version=score.schema_version,
            simulation_id=score.simulation_id,
            turn_n=score.turn_n,
            rubric_id=score.rubric_id,
            rubric_version=score.rubric_version,
            tenant_slug=score.tenant_slug,
            persona_kind=score.persona_kind,
            actor_profile_id=score.actor_profile_id,
            judges=judges_payload,
            round_1_score=score.round_1_score,
            round_2_score=score.round_2_score,
            final_score=score.final_score,
            round_1_variance=score.round_1_variance,
            round_2_variance=score.round_2_variance,
            debate_triggered=score.debate_triggered,
            unconverged=score.unconverged,
            r2_partial=score.r2_partial,
            suspicious=score.suspicious,
            injection_attempt_detected=score.injection_attempt_detected,
            cost_usd_total=score.cost_usd_total,
            latency_ms_total=score.latency_ms_total,
            cache_hit_count=score.cache_hit_count,
            metadata_={},
            created_at=score.created_at,
        )
        .on_conflict_do_nothing(
            index_elements=[
                EvalSimulatorGradeModel.simulation_id,
                EvalSimulatorGradeModel.turn_n,
                EvalSimulatorGradeModel.rubric_id,
            ],
        )
    )
    await session.execute(stmt)


@lru_cache(maxsize=8)
def _get_rubric_version(rubric_id: str) -> int:
    """Parse ``version: N`` from the YAML frontmatter of ``docs/specs/rubrics/{rubric_id}.md``.

    Process-scoped ``lru_cache`` — rubric MD is invariant within an eval run.
    Returns 1 on missing file or unparseable frontmatter (defensive default).
    """
    rubric_path = _RUBRICS_DIR / f"{rubric_id}.md"
    try:
        text = rubric_path.read_text(encoding="utf-8")
    except OSError:
        logger.warning("grader_rubric_md_missing", rubric_id=rubric_id, path=str(rubric_path))
        return 1

    # Frontmatter format (per existing rubrics) is a YAML block:
    # the line "version: N" appears under the YAML frontmatter wrapper.
    # We tolerate inline comments after the integer ("version: 1  # foo").
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("version:"):
            try:
                value = stripped.split(":", 1)[1].strip()
                # Strip inline comments like "1  # foo"
                value = value.split("#", 1)[0].strip()
                return int(value)
            except (IndexError, ValueError):
                logger.warning(
                    "grader_rubric_md_version_unparseable",
                    rubric_id=rubric_id,
                    line=stripped,
                )
                return 1

    logger.warning("grader_rubric_md_no_version_field", rubric_id=rubric_id)
    return 1


@lru_cache(maxsize=8)
def _read_rubric_md(rubric_id: str) -> str:
    """Read verbatim contents of ``docs/specs/rubrics/{rubric_id}.md`` (cached).

    Returns empty string on missing file (defensive — judge prompt builder
    accepts empty rubric_md_verbatim per its public contract).
    """
    rubric_path = _RUBRICS_DIR / f"{rubric_id}.md"
    try:
        return rubric_path.read_text(encoding="utf-8")
    except OSError:
        logger.warning("grader_rubric_md_read_failed", rubric_id=rubric_id, path=str(rubric_path))
        return ""


__all__ = [
    "JUDGE_CONCURRENCY",
    "VARIANCE_R1_THRESHOLD",
    "VARIANCE_R2_TARGET",
    "grade_transcript_maj_eval",
]
