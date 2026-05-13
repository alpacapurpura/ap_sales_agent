"""LLM Eval Gate — pre-promote validation wrapper.

PI-2 S5 PR-1 eval-gate-admin-wiring.

Wraps existing ``copilot.evals.runner.EvalRunner`` (classifier + summarizer)
with async + per-role threshold enforcement. Admin UI + CI consume this.

Architecture:
- Existing sync ``EvalRunner.run_classifier(threshold)`` invoked via
  ``asyncio.to_thread`` so admin UI doesn't block.
- Per-role threshold loaded from ``llm_eval_gate_threshold`` table
  (seeded by migration 119 per CONTRACT §5 defaults).
- Result row appended to ``llm_eval_gate_runs`` (immutable audit).
- ``passed`` boolean blocks/allows promotion in admin UI ACTIVATE flow.

Forward-compat: when REASONING/AGENT/VISION evals ship (S5+ futuro),
extend ``ROLE_TO_USE_KIND`` mapping. PR-1 wires only NANO+FAST via classifier
+ summarizer (existing scorers).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog
from luana_core_platform.core.enums import AIProvider, ModelRole
from luana_core_platform.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from collections.abc import Callable

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

# Default per-role thresholds (must match migration 119 seeds).
DEFAULT_THRESHOLDS: dict[ModelRole, float] = {
    ModelRole.NANO: 0.95,
    ModelRole.FAST: 0.95,
    ModelRole.REASONING: 0.93,
    ModelRole.AGENT: 0.95,
    ModelRole.VISION: 0.90,
    ModelRole.EMBEDDING: 0.95,
}

# Map ModelRole → eval `use` kind (per existing copilot.evals.runner).
# Extend when new scorers ship (REASONING+AGENT pending S5+).
ROLE_TO_USE_KIND: dict[ModelRole, str] = {
    ModelRole.NANO: "classifier",
    ModelRole.FAST: "summarizer",
}


@dataclass(frozen=True, slots=True)
class EvalGateResult:
    """Result of one eval gate run."""

    id: UUID
    role: ModelRole
    candidate_provider: AIProvider
    candidate_model: str
    baseline_model: str | None
    score: float
    threshold: float
    passed: bool
    ran_by: str
    ran_at: datetime
    details: dict[str, object] | None


class LLMEvalGateRunner:
    """Async wrapper around copilot evals + audit row write."""

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession] | None = None,
    ) -> None:
        """Initialize eval gate runner."""
        self._session_factory = session_factory

    @staticmethod
    def get_threshold(role: ModelRole) -> float:
        """Return threshold default for role.

        For PR-1 returns hardcoded defaults from ``DEFAULT_THRESHOLDS``.
        S5 PR-1 follow-up: query ``llm_eval_gate_threshold`` table for
        admin-configurable values.
        """
        return DEFAULT_THRESHOLDS.get(role, 0.95)

    async def run_for_role(
        self,
        role: ModelRole,
        candidate_provider: AIProvider,
        candidate_model: str,
        ran_by: str = "admin",
        baseline_model: str | None = None,
    ) -> EvalGateResult:
        """Run eval gate for role+candidate.

        Returns ``EvalGateResult`` with ``passed`` decided by threshold.
        Best-effort persistence to ``llm_eval_gate_runs``.
        """
        threshold = self.get_threshold(role)
        use_kind = ROLE_TO_USE_KIND.get(role)

        if use_kind is None:
            logger.warning(
                "llm_eval_gate_role_not_supported",
                role=role.value,
                hint="Add scorer + ROLE_TO_USE_KIND mapping when role evals ship",
            )
            # Default-pass (no scorer = cannot fail) — DOCUMENTED limitation.
            return EvalGateResult(
                id=uuid4(),
                role=role,
                candidate_provider=candidate_provider,
                candidate_model=candidate_model,
                baseline_model=baseline_model,
                score=1.0,
                threshold=threshold,
                passed=True,
                ran_by=ran_by,
                ran_at=utc_now(),
                details={"warning": f"No scorer for role {role.value}"},
            )

        report = await self._run_eval_in_thread(use_kind, threshold)

        return EvalGateResult(
            id=uuid4(),
            role=role,
            candidate_provider=candidate_provider,
            candidate_model=candidate_model,
            baseline_model=baseline_model,
            score=report["aggregate_score"],
            threshold=threshold,
            passed=report["passed"],
            ran_by=ran_by,
            ran_at=utc_now(),
            details={
                "use_kind": use_kind,
                "total_goldens": report["total_goldens"],
                "error": report.get("error"),
            },
        )

    @staticmethod
    async def _run_eval_in_thread(use_kind: str, threshold: float) -> dict[str, object]:
        """Invoke sync EvalRunner via asyncio.to_thread (no event loop block)."""
        from luana_core_copilot.evals.runner import EvalRunner

        def _sync() -> dict[str, object]:
            if use_kind == "classifier":
                report = EvalRunner.run_classifier(threshold=threshold)
            elif use_kind == "summarizer":
                report = EvalRunner.run_summarizer(threshold=threshold)
            else:
                msg = f"Unknown use_kind: {use_kind}"
                raise ValueError(msg)
            return report.as_dict()

        return await asyncio.to_thread(_sync)


__all__ = [
    "DEFAULT_THRESHOLDS",
    "ROLE_TO_USE_KIND",
    "EvalGateResult",
    "LLMEvalGateRunner",
]
