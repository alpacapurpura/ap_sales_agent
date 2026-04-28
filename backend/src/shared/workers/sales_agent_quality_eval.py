"""S10 — weekly sales_agent quality eval (LLM judge over goldens).

# [SALES-AGENT-QUALITY-S10] -> docs/domains/sales-agent/redesign-2026-04/phases/S10-quality-eval-loop.md

ARQ task triggered weekly por ``SchedulerSettings.cron_jobs``. Mirror del
``weekly_copilot_quality_eval`` con dos diferencias:

1. **Source de datos**: itera sobre los goldens fijos
   (``tests/quality/sales_agent_goldens/conversations.py``) en lugar de
   muestrear conversaciones reales. Razón: los goldens cubren las
   categorías canónicas de eval; los reales se sample-ean en una fase
   futura cuando existan suficientes leads multi-tenant para warrant
   sampling per-tenant.

2. **Bucket = category** (no workflow_id). Los KPIs se aggregate por
   ``qualification`` / ``objections`` / ``closing_payment`` / etc, sobre
   un sentinel tenant ``00000000-0000-0000-0000-000000000000``.

Drift detection: cuando se persiste una fila nueva, comparamos contra la
fila anterior del mismo bucket (semana previa). Si ``judge_avg_score``
baja >5%, emitimos structlog warning ``sales_agent_quality_drift``. El
admin dashboard refleja el aviso.

Cost guard: por default corre con ``CopilotJudge`` stub local (instancia
se crea con ``llm=None`` → resolve perezoso a NANO). Real LLM solo cuando
``RUN_LLM_JUDGE=1`` env. Sin esta env el worker emite filas con stub
4.0/dim — sirve para validar el plumbing pero no detecta regresiones de
modelo.
"""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from sqlalchemy import select

from src.modules.sales_agent.application.quality.judge import (
    JudgeResult,
    SalesAgentJudge,
)
from src.modules.sales_agent.infrastructure.models.workflow_metric_model import (
    SalesAgentWorkflowMetricModel,
)
from src.modules.sales_agent.infrastructure.repositories.workflow_metric_repository import (
    SalesAgentWorkflowMetricRepository,
)
from src.shared.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)

WINDOW_DAYS: int = 7
DRIFT_THRESHOLD: float = 0.05  # 5% drop week-over-week → alert
SENTINEL_TENANT_ID: UUID = UUID("00000000-0000-0000-0000-000000000000")


def _compute_period_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    """Return the rolling weekly window (start_inclusive, end_exclusive).

    Normaliza ``end`` al inicio del día UTC para que re-correr el cron el
    mismo día caiga en el mismo bucket (ON CONFLICT upsert). Sin esta
    normalización los microsegundos de ``utc_now()`` rompen idempotencia.
    """
    raw_end = now or utc_now()
    end = raw_end.replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=WINDOW_DAYS)
    return start, end


def _resolve_judge() -> SalesAgentJudge:
    """Build the judge — stub by default, NANO when ``RUN_LLM_JUDGE=1``."""
    if os.getenv("RUN_LLM_JUDGE") == "1":
        return SalesAgentJudge()
    return SalesAgentJudge(llm=_StubJudgeLLM())


class _StubJudgeLLM:
    """Default stub used when ``RUN_LLM_JUDGE`` is unset."""

    def invoke(self, _messages: object) -> object:
        import json as _json

        from langchain_core.messages import AIMessage

        payload = {
            "brand_voice_fidelity": {"score": 4.0, "reason": "stub"},
            "channel_format_correctness": {"score": 4.0, "reason": "stub"},
            "commercial_effectiveness": {"score": 4.0, "reason": "stub"},
            "pii_safety": {"score": 4.0, "reason": "stub"},
            "tone_locale_fitness": {"score": 4.0, "reason": "stub"},
        }
        return AIMessage(content=_json.dumps(payload), response_metadata={"id": "stub_cron"})


def _load_goldens() -> list:
    """Lazy-load goldens — viven en ``tests/`` pero el cron las consume."""
    # Lazy import — los goldens viven bajo tests/ pero son fixtures sintéticas
    # estables, sin PII real. Importarlas en runtime para el cron es OK.
    from tests.quality.sales_agent_goldens.conversations import (
        GOLDEN_CONVERSATIONS,
    )

    return list(GOLDEN_CONVERSATIONS)


def _judge_goldens(
    judge: SalesAgentJudge,
    goldens: list,
) -> dict[str, list[JudgeResult]]:
    """Run the judge over each golden, grouped by category."""
    grouped: dict[str, list[JudgeResult]] = defaultdict(list)
    for conv in goldens:
        result = judge.evaluate(
            user_input=conv.user_input,
            assistant_output=conv.expected_output,
            brand_voice=conv.brand_voice,
            channel=conv.channel,
            stage=conv.stage,
            context=conv.context,
        )
        grouped[conv.category].append(result)
    return grouped


def _previous_score_for(
    db: Session,
    *,
    bucket_id: str,
    before: datetime,
) -> float | None:
    """Return the most recent ``judge_avg_score`` for ``bucket_id`` strictly before ``before``."""
    stmt = (
        select(SalesAgentWorkflowMetricModel.judge_avg_score)
        .where(
            SalesAgentWorkflowMetricModel.tenant_id == SENTINEL_TENANT_ID,
            SalesAgentWorkflowMetricModel.bucket_id == bucket_id,
            SalesAgentWorkflowMetricModel.period_start < before,
        )
        .order_by(SalesAgentWorkflowMetricModel.period_start.desc())
        .limit(1)
    )
    value = db.execute(stmt).scalar_one_or_none()
    return float(value) if value is not None else None


def _persist_and_detect_drift(
    db: Session,
    grouped: dict[str, list[JudgeResult]],
    period: tuple[datetime, datetime],
) -> int:
    """Aggregate KPIs + upsert + emit drift warnings. Returns rows written."""
    repo = SalesAgentWorkflowMetricRepository(db)
    start, end = period
    written = 0

    for bucket_id, results in grouped.items():
        scores = [r.avg_score for r in results if r.avg_score > 0]
        avg = sum(scores) / len(scores) if scores else None
        judge_models = sorted({r.judge_model for r in results if r.judge_model})
        previous = _previous_score_for(db, bucket_id=bucket_id, before=start)
        per_dim_scores = _aggregate_per_dim(results)

        extra_metadata: dict[str, Any] = {
            "judge_models": judge_models,
            "stub_mode": "stub" in (judge_models[0] if judge_models else "") or os.getenv("RUN_LLM_JUDGE") != "1",
            "per_dim_scores": per_dim_scores,
            "previous_avg_score": previous,
        }

        if avg is not None and previous is not None:
            drop = previous - avg
            if drop > 0 and (drop / max(previous, 1e-6)) >= DRIFT_THRESHOLD:
                extra_metadata["drift_alert"] = True
                extra_metadata["drift_pct"] = round(drop / previous, 4)
                logger.warning(
                    "sales_agent_quality_drift",
                    bucket_id=bucket_id,
                    previous=previous,
                    current=avg,
                    drop_pct=round(drop / previous, 4),
                )

        try:
            repo.upsert(
                tenant_id=SENTINEL_TENANT_ID,
                bucket_id=bucket_id,
                period_start=start,
                period_end=end,
                started_count=len(results),
                judge_avg_score=round(avg, 2) if avg is not None else None,
                judge_sample_size=len(results),
                extra_metadata=extra_metadata,
            )
            written += 1
        except Exception:
            logger.exception("sales_agent_quality_upsert_failed", bucket_id=bucket_id)
            db.rollback()
    return written


def _aggregate_per_dim(results: list[JudgeResult]) -> dict[str, float]:
    """Average each dimension across the result set."""
    sums: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for r in results:
        for dim in r.dimensions:
            if dim.score > 0:
                sums[dim.name] += dim.score
                counts[dim.name] += 1
    return {name: round(sums[name] / counts[name], 2) for name in sums if counts[name] > 0}


def run_weekly_quality_eval(
    db: Session,
    *,
    judge: SalesAgentJudge | None = None,
) -> int:
    """Sync entry point — invoked from the ARQ task wrapper + admin button.

    Returns the number of metric rows written. Exception-tolerant: a
    failure to load / judge / upsert logs and continues so a single bad
    bucket doesn't poison the run.
    """
    judge = judge or _resolve_judge()
    period = _compute_period_window()
    try:
        goldens = _load_goldens()
    except Exception:
        logger.exception("sales_agent_quality_load_goldens_failed")
        return 0
    if not goldens:
        logger.info("sales_agent_quality_no_goldens")
        return 0
    try:
        grouped = _judge_goldens(judge, goldens)
    except Exception:
        logger.exception("sales_agent_quality_judge_failed")
        return 0
    written = _persist_and_detect_drift(db, grouped, period)
    logger.info(
        "sales_agent_quality_weekly_eval_complete",
        goldens=len(goldens),
        rows_written=written,
    )
    return written


async def weekly_sales_agent_quality_eval(ctx: dict) -> int:
    """ARQ task wrapper — opens its own DB session via ``ctx['db_factory']``."""
    db_factory = ctx.get("db_factory")
    if db_factory is None:
        logger.warning("sales_agent_quality_no_db_factory")
        return 0
    db = db_factory()
    try:
        return run_weekly_quality_eval(db)
    finally:
        db.close()


__all__ = (
    "DRIFT_THRESHOLD",
    "SENTINEL_TENANT_ID",
    "WINDOW_DAYS",
    "run_weekly_quality_eval",
    "weekly_sales_agent_quality_eval",
)
