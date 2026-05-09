"""Cache for MAJ-EVAL grades — hash composition + lookup/persist (Story E T-6).

D8 cement: cache key = sha256(canonical JSON of 5-field composition):
    judge_set_hash, rubric_id, rubric_version, tenant_voice_hash, transcript_hash.

Composition order is FROZEN — drift breaks idempotency cement.

D16 cement (cache invalidation precision):
    - rubric MD edit → version bump → key changes → cache miss → re-grade
    - tenant voice edit → tenant_voice_hash changes → key changes
    - judge weights edit → judge_set_hash changes → key changes
    - transcript byte-equal (Story B determinism) → transcript_hash same → cache HIT

Graceful Degradation Rule 2 (`tessl__graceful-degradation`):
    DB unavailable in lookup → log warn + return None (NOT raise).
    DB unavailable in persist → log warn + skip (NOT raise).
    Cache failures NEVER bubble out to the MAJ-EVAL state machine — re-grade is
    always a safe fallback (slower, but correct).

Decisions applicable: D8 (5-field composition), D9 (cache table separate),
D16 (auto-invalidation), D-BE-2 (cache table separate), D-BE-6 (sha256 64-char).
"""

# voseo-allowed: docstring cita es-AR voseo en transcript subject (sales_agent voice exception)

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Final

import structlog
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_simulator_grade_cache import (
    EvalSimulatorGradeCacheModel,
)
from tests.agentic_evals.sales_agent.grader.result import MajEvalScore

logger = structlog.get_logger(__name__)


# Composition order — D8 cement frozen alphabetical.
# ANY change to this composition breaks cache idempotency across deploys.
_CACHE_KEY_FIELDS: Final[tuple[str, ...]] = (
    "judge_set_hash",
    "rubric_id",
    "rubric_version",
    "tenant_voice_hash",
    "transcript_hash",
)


# ──────────────────────────────────────────────────────────────────────────────
# Hash composition (pure)
# ──────────────────────────────────────────────────────────────────────────────


def compute_cache_key(
    *,
    transcript_hash: str,
    rubric_id: str,
    rubric_version: int,
    tenant_voice_hash: str,
    judge_set_hash: str,
) -> str:
    """Compose a deterministic 64-char sha256 hex cache key (D8 cement).

    Composition order is FROZEN alphabetical (per ``_CACHE_KEY_FIELDS``):
    ``judge_set_hash`` → ``rubric_id`` → ``rubric_version`` → ``tenant_voice_hash``
    → ``transcript_hash``. Drift in this composition silently breaks idempotency.

    Invalidation precision (D16):
        * rubric MD edit → version bump → key changes → cache miss → re-grade
        * tenant voice edit → ``tenant_voice_hash`` changes → key changes
        * judge weights edit → ``judge_set_hash`` changes → key changes
        * transcript byte-equal (Story B determinism) → ``transcript_hash`` same → HIT
    """
    payload = {
        "judge_set_hash": judge_set_hash,
        "rubric_id": rubric_id,
        "rubric_version": rubric_version,
        "tenant_voice_hash": tenant_voice_hash,
        "transcript_hash": transcript_hash,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def compute_transcript_hash(transcript: list[Any]) -> str:
    """sha256 of transcript role+turn_number+content concatenation.

    Duck-typed: each item must expose ``role``, ``turn_number``, ``content`` (Story D
    GoldenTurnModel). Pure function — Story B byte-equal determinism implies
    same transcript bytes → same hash → cache HIT.
    """
    body = "\n".join(f"[{turn.role}:{turn.turn_number}]:{turn.content}" for turn in transcript).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def compute_tenant_voice_hash(voice_profile: Any) -> str:
    """sha256 of ``personality_profile.system_instruction`` verbatim.

    Reads the SSoT field directly per sales-agent-expert §3 cement
    (READ-ONLY — NEVER mutate, distill, mirror, or fine-tune).
    """
    body = voice_profile.system_instruction.encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def compute_judge_set_hash(weights: dict[str, float]) -> str:
    """sha256 of judge_id+weight pairs (D2 cement: 0.4/0.4/0.2 for sonnet/gpt4o/kimi).

    Insertion order does NOT matter — ``sort_keys=True`` produces a canonical
    representation. Bumping any weight changes the hash → cache invalidates
    automatically (D16 precision).
    """
    canonical = json.dumps(weights, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# Cache lookup / persist (DB CRUD with graceful degradation)
# ──────────────────────────────────────────────────────────────────────────────


async def cache_lookup(session: AsyncSession, cache_key: str) -> MajEvalScore | None:
    """Return the cached ``MajEvalScore`` for ``cache_key`` or ``None`` on miss.

    On HIT: reconstruct the Pydantic model from the JSONB payload + bump
    ``last_hit_at = utc_now()`` (audit trail for cache hit ratio analysis per D11).

    On MISS: return ``None``.

    On DB unavailable: log structured warning (`grader_cache_lookup_failed`) +
    return ``None`` per Graceful Degradation Rule 2. NEVER raises — caller falls
    back to a fresh grade.
    """
    try:
        stmt = select(EvalSimulatorGradeCacheModel).where(
            EvalSimulatorGradeCacheModel.cache_key == cache_key,
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()

        if row is None:
            return None

        score = MajEvalScore.model_validate(row.payload)

        # Update last_hit_at — best-effort audit (do not surface failure to caller)
        try:
            await session.execute(
                update(EvalSimulatorGradeCacheModel)
                .where(EvalSimulatorGradeCacheModel.cache_key == cache_key)
                .values(last_hit_at=datetime.now(timezone.utc)),
            )
        except Exception as exc:  # noqa: BLE001 — best-effort audit metadata
            logger.warning(
                "grader_cache_last_hit_update_failed",
                dependency="eval_simulator_grade_cache",
                cache_key_prefix=cache_key[:16],
                error=str(exc),
            )

        return score

    except Exception as exc:  # noqa: BLE001 — graceful degradation Rule 2
        logger.warning(
            "grader_cache_lookup_failed",
            dependency="eval_simulator_grade_cache",
            cache_key_prefix=cache_key[:16],
            error=str(exc),
            fallback="re-grade",
        )
        return None


async def cache_persist(
    *,
    session: AsyncSession,
    cache_key: str,
    score: MajEvalScore,
    transcript_hash: str,
    rubric_id: str,
    rubric_version: int,
    tenant_voice_hash: str,
    judge_set_hash: str,
) -> None:
    """Persist ``score`` under ``cache_key`` (idempotent first-writer-wins).

    Uses ``INSERT ... ON CONFLICT DO NOTHING`` — same key composition produces
    same content (D8 cement), so the second writer's payload is intentionally
    discarded. This guards against race conditions in concurrent eval runs.

    On DB unavailable: log structured warning (`grader_cache_persist_failed`) +
    skip per Graceful Degradation Rule 2. NEVER raises — the grade row in
    ``eval_simulator_grade`` remains the source of truth; cache is an optimization.
    """
    payload = score.model_dump(mode="json")

    try:
        stmt = (
            pg_insert(EvalSimulatorGradeCacheModel)
            .values(
                cache_key=cache_key,
                schema_version=score.schema_version,
                transcript_hash=transcript_hash,
                rubric_id=rubric_id,
                rubric_version=rubric_version,
                tenant_voice_hash=tenant_voice_hash,
                judge_set_hash=judge_set_hash,
                payload=payload,
                created_at=datetime.now(timezone.utc),
                last_hit_at=None,
            )
            .on_conflict_do_nothing(index_elements=[EvalSimulatorGradeCacheModel.cache_key])
        )
        await session.execute(stmt)

    except Exception as exc:  # noqa: BLE001 — graceful degradation Rule 2
        logger.warning(
            "grader_cache_persist_failed",
            dependency="eval_simulator_grade_cache",
            cache_key_prefix=cache_key[:16],
            rubric_id=rubric_id,
            rubric_version=rubric_version,
            error=str(exc),
            fallback="skip-cache",
        )
