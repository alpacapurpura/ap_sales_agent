"""Integration adapter — wraps grade_transcript_maj_eval as a run_simulation callback (Story E T-9).

Reference impl: ``docs/product/stories/sales-agent-voice-fidelity-grader-runtime/03-arch.md§4.8``.

Design contract
===============

The Story B ``run_simulation`` orchestrator (``simulator/_internal/runner.py``)
exposes an OPTIONAL ``grader_callback`` parameter. T-9 wires the grader to that
hook via :func:`make_grader_callback` — a factory returning an async callable
that builds :class:`RubricGradeRequest` from the :class:`SimulationResult` and
invokes :func:`grade_transcript_maj_eval` (Story E H9 expand 7→8 public surface).

Cement decisions
================

* **D17 / DQ5** — async via ``asyncio.create_task`` fire-and-forget. The
  callback is scheduled by the runner POST-completion; the runner does NOT
  await. Preserves Story B determinism + latency budget cement.
* **D-AG-10** — DB write best-effort: callback wraps the grader invocation
  in ``try/except`` + ``structlog.warning``. NEVER propagates exceptions
  back to the simulation loop (graceful degradation Rule 2).
* **D7 / D-AG-11** — rubric set dispatch by ``persona_kind``: this adapter
  surfaces ``rubrics`` as a parameter so Stories F/G/I can dispatch the
  correct rubric subset per the persona running.
* **D-AG-17** — judges dispatch via LiteLLM Proxy ONLY. This adapter does
  NOT touch any LLM client directly — it delegates to
  :func:`grade_transcript_maj_eval`, which uses the canonical path.
* **anti-duplication §0** — REUSE :class:`RubricGradeRequest` (Story E T-2
  cement) and :func:`grade_transcript_maj_eval` (Story E T-5 public API).
  No mirror layer.

# voseo-allowed: docstring quotes architectural cement decisions
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import structlog

from tests.agentic_evals.sales_agent.grader._internal.maj_eval import (
    grade_transcript_maj_eval,
)
from tests.agentic_evals.sales_agent.grader.result import RubricGradeRequest

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from tests.agentic_evals.sales_agent.simulator._internal.observability import (
        EvalSimulatorObservabilityContext,
    )
    from tests.agentic_evals.sales_agent.simulator.result import SimulationResult

logger = structlog.get_logger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Default rubric sets per persona_kind (D7 cement)
# ──────────────────────────────────────────────────────────────────────────────


_RUBRICS_HAPPY: tuple[str, ...] = (
    "voice-fidelity",
    "no-overpromise",
    "no-hallucination",
)
"""Happy persona — 3 rubrics (qualification-accuracy NOT applicable)."""


_RUBRICS_NURTURE_OR_UNQUALIFIED: tuple[str, ...] = (
    "voice-fidelity",
    "qualification-accuracy",
    "no-overpromise",
    "no-hallucination",
)
"""Nurture / unqualified personas — 4 rubrics including qualification-accuracy."""


_RUBRICS_DEFAULT: tuple[str, ...] = _RUBRICS_NURTURE_OR_UNQUALIFIED
"""Conservative default — 4 rubrics. Story I extends with toxicity-control."""


def _rubrics_for_persona_kind(persona_kind: str) -> tuple[str, ...]:
    """Return the canonical rubric subset for a given persona_kind (D7 cement)."""
    if persona_kind == "happy":
        return _RUBRICS_HAPPY
    if persona_kind in {"nurture", "unqualified"}:
        return _RUBRICS_NURTURE_OR_UNQUALIFIED
    # adversarial → Story I extends; for v1 use the 4-rubric set as a safe default.
    return _RUBRICS_DEFAULT


# ──────────────────────────────────────────────────────────────────────────────
# Public factory — make_grader_callback
# ──────────────────────────────────────────────────────────────────────────────


def make_grader_callback(
    *,
    session: AsyncSession,
    obs_context: EvalSimulatorObservabilityContext,
    tenant_voice_profile: Any,
    rubrics: tuple[str, ...] | list[str] | None = None,
    cache_policy: str = "use",
) -> Callable[..., Any]:
    """Build a fire-and-forget grader callback compatible with ``run_simulation``.

    The returned coroutine accepts a :class:`SimulationResult` and invokes
    :func:`grade_transcript_maj_eval` with a derived :class:`RubricGradeRequest`.
    Failures inside the callback are logged via ``structlog.warning`` and
    swallowed — they never propagate to the runner's ``asyncio.create_task``
    scheduler (graceful degradation Rule 2).

    Parameters
    ----------
    session:
        Async SQLAlchemy session for grade + cache writes. Must outlive the
        callback invocation (caller responsibility).
    obs_context:
        Story B :class:`EvalSimulatorObservabilityContext` — passed verbatim
        to the grader so cost / observability rows fire under the eval cost
        bucket (H7 cement).
    tenant_voice_profile:
        Tenant ``personality_profile.system_instruction`` carrier — duck-typed
        per ``cache.compute_tenant_voice_hash`` contract. READ-ONLY consumption
        (sales-agent-expert §3 SSoT cement).
    rubrics:
        Optional rubric subset override. ``None`` (default) dispatches by
        ``result.persona_kind`` per D7 cement.
    cache_policy:
        ``"use"`` (default) consults ``eval_simulator_grade_cache``; ``"bypass"``
        forces re-grading. Forwarded verbatim to :class:`RubricGradeRequest`.

    Returns
    -------
    Callable[[SimulationResult], Awaitable[None]]:
        An async callable suitable for ``run_simulation(grader_callback=...)``.

    Notes
    -----
    The callback derives ``persona_kind`` from
    ``result.actor_profile.persona_kind`` when available (Story C cement),
    falling back to the ``actor_profile_id`` heuristic when the field is
    absent. Story D goldens supply ``persona_kind`` directly.
    """
    chosen_rubrics: tuple[str, ...] | None = tuple(rubrics) if rubrics is not None else None

    async def _callback(result: SimulationResult) -> None:
        """Wrap :func:`grade_transcript_maj_eval` invocation per turn batch.

        Best-effort: any failure logs a structured warning with simulation
        identity + error class. NEVER raises out — Story B determinism
        cement + ``run_simulation`` fire-and-forget contract.
        """
        try:
            persona_kind = _resolve_persona_kind(result)
            actor_profile_id = _resolve_actor_profile_id(result)
            tenant_slug = _resolve_tenant_slug(result)

            rubric_subset = chosen_rubrics if chosen_rubrics is not None else _rubrics_for_persona_kind(persona_kind)

            request = RubricGradeRequest(
                transcript=list(result.transcript),
                tenant_voice_profile=tenant_voice_profile,
                rubrics=list(rubric_subset),  # type: ignore[arg-type]
                simulation_id=str(result.simulation_id),
                tenant_slug=tenant_slug,
                persona_kind=persona_kind,  # type: ignore[arg-type]
                actor_profile_id=actor_profile_id,
                cache_policy=cache_policy,  # type: ignore[arg-type]
            )

            scores = await grade_transcript_maj_eval(
                request,
                session=session,
                obs_context=obs_context,
            )

            logger.info(
                "grader_callback_completed",
                simulation_id=request.simulation_id,
                tenant_slug=tenant_slug,
                persona_kind=persona_kind,
                rubrics_count=len(rubric_subset),
                turns_count=len(result.transcript),
                grades_persisted=len(scores),
            )
        except Exception as exc:  # noqa: BLE001 — Rule 2 graceful degradation
            logger.warning(
                "grader_callback_failed",
                simulation_id=str(getattr(result, "simulation_id", "<unknown>")),
                error_class=type(exc).__name__,
                error=str(exc),
                fallback="skip-grade",
            )

    return _callback


# ──────────────────────────────────────────────────────────────────────────────
# Helpers — duck-typed extraction from SimulationResult
# ──────────────────────────────────────────────────────────────────────────────


def _resolve_persona_kind(result: SimulationResult) -> str:
    """Best-effort extraction of ``persona_kind`` from a SimulationResult.

    Priority:
    1. ``result.actor_profile.persona_kind`` (Story C cement field).
    2. Heuristic match on ``result.actor_profile_id``.
    3. Fallback "happy".
    """
    actor_profile = getattr(result, "actor_profile", None)
    if actor_profile is not None:
        kind = getattr(actor_profile, "persona_kind", None)
        if isinstance(kind, str) and kind:
            return kind

    actor_id = getattr(result, "actor_profile_id", "") or ""
    actor_id_lower = actor_id.lower()
    for candidate in ("happy", "nurture", "unqualified", "adversarial"):
        if candidate in actor_id_lower:
            return candidate
    return "happy"


def _resolve_actor_profile_id(result: SimulationResult) -> str:
    """Best-effort extraction of ``actor_profile_id`` from a SimulationResult."""
    actor_id = getattr(result, "actor_profile_id", None)
    if isinstance(actor_id, str) and actor_id:
        return actor_id
    actor_profile = getattr(result, "actor_profile", None)
    if actor_profile is not None:
        nested = getattr(actor_profile, "id", None)
        if isinstance(nested, str) and nested:
            return nested
    return "unknown"


def _resolve_tenant_slug(result: SimulationResult) -> str:
    """Best-effort extraction of ``tenant_slug`` from a SimulationResult.

    Priority:
    1. Explicit ``result.tenant_slug`` if Story F bumps SimulationResult later.
    2. ``result.archetype_slug`` (Story B cement — 5 ratified archetypes
       align with Story D 5 tenant slugs by direct slug match).
    3. Fallback "tenant_unknown".
    """
    tenant_slug = getattr(result, "tenant_slug", None)
    if isinstance(tenant_slug, str) and tenant_slug:
        return tenant_slug
    archetype_slug = getattr(result, "archetype_slug", None)
    if isinstance(archetype_slug, str) and archetype_slug:
        return archetype_slug
    return "tenant_unknown"


__all__ = [
    "make_grader_callback",
]
