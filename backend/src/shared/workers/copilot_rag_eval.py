"""F11.5 — weekly RAG retrieval eval over the curated marketing KB.

# [COPILOT-RAG-EVAL-F11] -> docs/domains/copilot/redesign-2026-04/learnings/F11-housekeeping.md

Mirrors :func:`src.shared.workers.copilot_quality_eval.run_weekly_quality_eval`
but evaluates RAG retrieval quality against the canonical golden set
(``RAG_GOLDENS``) instead of sampled live conversations.

Per golden:

1. ``MarketingKbStore.search(question)`` (real KB on Mondays, stub in CI).
2. ``retrieval_recall``: 1.0 if ``expected_source_doc`` appears in the
   top-K, else 0.0.
3. ``kb_citations``: distinct ``source_doc`` values returned.
4. ``retrieval_latency_ms``: wall-clock latency of the ``search`` call.
5. ``CopilotJudge`` over (question, expected_answer_excerpt, retrieved
   context) using the RAG-specific dimensions
   (``retrieval_relevance`` / ``citation_accuracy`` /
   ``answer_groundedness`` / ``completeness``).

Aggregated into a single row per run (sentinel ``tenant_id`` + workflow
``_rag_eval``) so the admin ``/copilot-quality`` page can read a per-week
trend without joining sample-level data.

Cost guard: 8 goldens x 1 NANO judge call per week ~ 8 calls / month ~
$0.001. Negligible.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from luana_core_copilot.application.observability.judge import (
    CopilotJudge,
    JudgeResult,
)
from luana_core_copilot.application.observability.rag_goldens import (
    RAG_DIMENSIONS,
    RAG_GOLDENS,
    RagGolden,
)
from luana_core_copilot.application.tools.knowledge_search import (
    knowledge_search_impl,
)
from luana_core_copilot.infrastructure.repositories.workflow_metric_repository import (
    WorkflowMetricRepository,
)
from luana_core_platform.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from collections.abc import Iterable

    from sqlalchemy.orm import Session


logger = structlog.get_logger(__name__)

WINDOW_DAYS: int = 7
RAG_WORKFLOW_ID: str = "_rag_eval"

# Tenant-agnostic sentinel — RAG corpus is global. ``tenant_id`` is
# ``nullable=False`` on ``copilot_workflow_metric`` so we use the canonical
# nil UUID instead of leaving the row unbucketed.
RAG_SENTINEL_TENANT: UUID = UUID(int=0)


@dataclass(frozen=True, slots=True)
class _GoldenResult:
    """Per-golden eval outcome — aggregated across the run."""

    golden_id: str
    expected_source_doc: str
    retrieval_recall: float
    retrieval_latency_ms: int
    citations: tuple[str, ...]
    judge_result: JudgeResult


def _compute_period_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    """Return the rolling weekly window (start_inclusive, end_exclusive)."""
    end = now or utc_now()
    start = end - timedelta(days=WINDOW_DAYS)
    return start, end


def _evaluate_golden(
    golden: RagGolden,
    *,
    store: object,
    judge: CopilotJudge,
    limit: int = 5,
) -> _GoldenResult:
    """Run retrieval + judge for one golden. All exceptions surface to caller."""
    started = time.monotonic()
    chunks = store.search(golden.question, limit=limit)  # type: ignore[attr-defined]
    latency_ms = int((time.monotonic() - started) * 1000)

    citations = tuple(
        dict.fromkeys(str(chunk.get("source_doc")) for chunk in chunks if chunk.get("source_doc")),
    )
    recall = 1.0 if golden.expected_source_doc in citations else 0.0

    retrieved_md = knowledge_search_impl(golden.question, store=store)
    judge_result = judge.evaluate(
        user_input=golden.question,
        assistant_output=golden.expected_answer_excerpt,
        context=retrieved_md,
    )

    return _GoldenResult(
        golden_id=golden.id,
        expected_source_doc=golden.expected_source_doc,
        retrieval_recall=recall,
        retrieval_latency_ms=latency_ms,
        citations=citations,
        judge_result=judge_result,
    )


def _aggregate(results: Iterable[_GoldenResult]) -> dict[str, Any]:
    """Reduce per-golden results into the JSONB shape persisted weekly."""
    results_list = list(results)
    if not results_list:
        return {
            "golden_count": 0,
            "retrieval_recall_avg": None,
            "retrieval_latency_ms_avg": None,
            "kb_citations": [],
            "judge_dimensions": {},
            "per_golden_recall": {},
            "judge_models": [],
        }

    recalls = [r.retrieval_recall for r in results_list]
    latencies = [r.retrieval_latency_ms for r in results_list]
    citations: list[str] = []
    seen: set[str] = set()
    for r in results_list:
        for src in r.citations:
            if src not in seen:
                seen.add(src)
                citations.append(src)

    dim_totals: dict[str, list[float]] = {dim: [] for dim in RAG_DIMENSIONS}
    for r in results_list:
        for dim in r.judge_result.dimensions:
            if dim.name in dim_totals and dim.score > 0:
                dim_totals[dim.name].append(dim.score)
    judge_dim_avg = {dim: round(sum(scores) / len(scores), 2) if scores else None for dim, scores in dim_totals.items()}

    judge_models = sorted(
        {r.judge_result.judge_model for r in results_list if r.judge_result.judge_model},
    )

    return {
        "golden_count": len(results_list),
        "retrieval_recall_avg": round(sum(recalls) / len(recalls), 3),
        "retrieval_latency_ms_avg": int(sum(latencies) / len(latencies)),
        "kb_citations": citations,
        "judge_dimensions": judge_dim_avg,
        "per_golden_recall": {r.golden_id: r.retrieval_recall for r in results_list},
        "judge_models": judge_models,
    }


def _resolve_default_store() -> object:
    """Lazy build the production marketing KB store.

    Kept indirect so unit tests can pass an injected stub without forcing
    Qdrant connections at import time (heredado F4 gotcha).
    """
    from luana_core_copilot.infrastructure.qdrant.marketing_kb_store import (
        MarketingKbStore,
    )

    return MarketingKbStore()


def run_weekly_rag_eval(
    db: Session,
    *,
    store: object | None = None,
    judge: CopilotJudge | None = None,
    goldens: tuple[RagGolden, ...] = RAG_GOLDENS,
) -> int:
    """Sync entry point — invoked from the ARQ task wrapper + admin button.

    Returns the number of metric rows written (0 or 1). Exception-tolerant:
    a failure to retrieve / judge / upsert logs and continues so a single
    bad golden doesn't poison the run.
    """
    judge = judge or CopilotJudge(dimensions=RAG_DIMENSIONS)
    kb_store = store if store is not None else _resolve_default_store()
    period = _compute_period_window()

    results: list[_GoldenResult] = []
    failed: list[str] = []
    for golden in goldens:
        try:
            results.append(_evaluate_golden(golden, store=kb_store, judge=judge))
        except Exception as exc:  # noqa: BLE001 — per-golden resilience
            logger.warning(
                "copilot_rag_eval_golden_failed",
                golden_id=golden.id,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            failed.append(golden.id)

    if not results:
        logger.info("copilot_rag_eval_no_results", failed_count=len(failed))
        return 0

    aggregate = _aggregate(results)
    aggregate["failed_golden_ids"] = failed

    judge_avg = None
    judge_dim_scores = [score for score in aggregate["judge_dimensions"].values() if score is not None]
    if judge_dim_scores:
        judge_avg = round(sum(judge_dim_scores) / len(judge_dim_scores), 2)

    repo = WorkflowMetricRepository(db)
    try:
        repo.upsert(
            tenant_id=RAG_SENTINEL_TENANT,
            workflow_id=RAG_WORKFLOW_ID,
            period_start=period[0],
            period_end=period[1],
            started_count=len(results),
            completed_count=len(results),
            abandoned_count=len(failed),
            avg_turns_to_completion=None,
            judge_avg_score=judge_avg,
            judge_sample_size=len(results),
            extra_metadata=aggregate,
        )
    except Exception:
        logger.exception("copilot_rag_eval_upsert_failed")
        return 0

    logger.info(
        "copilot_rag_eval_complete",
        golden_count=len(results),
        failed=len(failed),
        retrieval_recall_avg=aggregate["retrieval_recall_avg"],
        judge_avg=judge_avg,
    )
    return 1


async def weekly_copilot_rag_eval(ctx: dict) -> int:
    """ARQ task wrapper — opens its own DB session via ``ctx['db_factory']``."""
    db_factory = ctx.get("db_factory")
    if db_factory is None:
        logger.warning("copilot_rag_eval_no_db_factory")
        return 0
    db = db_factory()
    try:
        return run_weekly_rag_eval(db)
    finally:
        db.close()


__all__ = (
    "RAG_SENTINEL_TENANT",
    "RAG_WORKFLOW_ID",
    "WINDOW_DAYS",
    "run_weekly_rag_eval",
    "weekly_copilot_rag_eval",
)
