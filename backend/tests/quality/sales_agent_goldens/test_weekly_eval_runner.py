"""S10 — weekly_sales_agent_quality_eval cron tests.

# [SALES-AGENT-QUALITY-S10] -> docs/domains/sales-agent/redesign-2026-04/phases/S10-quality-eval-loop.md

Cobertura:

* ``run_weekly_quality_eval`` con stub judge persiste 1 row per category.
* Idempotencia: re-run mismo período → ON CONFLICT upsert (sin duplicados).
* Drift detection: si previous score baja >5% → ``drift_alert=True``.
* Cron registrado en ``WorkerSettings.functions`` y
  ``SchedulerSettings.cron_jobs`` (smoke import).

Usa el fixture global ``db`` de :mod:`backend.tests.conftest` — SQLite
in-memory con todos los modelos registrados, transaction-rollback per-test.
"""

from __future__ import annotations

import json

from langchain_core.messages import AIMessage
from sqlalchemy import select

from luana_core_sales_agent.application.quality.judge import SalesAgentJudge
from luana_core_sales_agent.infrastructure.models.workflow_metric_model import (
    SalesAgentWorkflowMetricModel,
)
from src.shared.workers.sales_agent_quality_eval import (
    DRIFT_THRESHOLD,
    SENTINEL_TENANT_ID,
    run_weekly_quality_eval,
)
from tests.quality.sales_agent_goldens.conversations import CATEGORIES


class _ScoredStubLLM:
    """Stub LLM whose payload score is configurable per call."""

    def __init__(self, score: float):
        self.score = score

    def invoke(self, _messages):
        payload = {
            "brand_voice_fidelity": {"score": self.score, "reason": "ok"},
            "channel_format_correctness": {"score": self.score, "reason": "ok"},
            "commercial_effectiveness": {"score": self.score, "reason": "ok"},
            "pii_safety": {"score": self.score, "reason": "ok"},
            "tone_locale_fitness": {"score": self.score, "reason": "ok"},
        }
        return AIMessage(content=json.dumps(payload), response_metadata={"id": "stub"})


def test_run_weekly_quality_eval_persists_one_row_per_category(db):
    judge = SalesAgentJudge(llm=_ScoredStubLLM(score=4.0))
    written = run_weekly_quality_eval(db, judge=judge)
    assert written == len(CATEGORIES)

    rows = db.execute(select(SalesAgentWorkflowMetricModel)).scalars().all()
    bucket_ids = {row.bucket_id for row in rows}
    assert bucket_ids == set(CATEGORIES)
    for row in rows:
        assert row.tenant_id == SENTINEL_TENANT_ID
        assert row.judge_avg_score is not None
        assert row.judge_sample_size > 0
        assert row.extra_metadata is not None
        assert "per_dim_scores" in row.extra_metadata


def test_run_weekly_quality_eval_idempotent_on_same_period(db):
    """Re-correr el cron en el mismo período → ON CONFLICT upsert, sin duplicados."""
    judge = SalesAgentJudge(llm=_ScoredStubLLM(score=4.0))
    run_weekly_quality_eval(db, judge=judge)
    run_weekly_quality_eval(db, judge=judge)

    rows = db.execute(select(SalesAgentWorkflowMetricModel)).scalars().all()
    assert len(rows) == len(CATEGORIES), "Esperaba 1 row per categoria post-upsert, no duplicados."


def test_drift_detection_emits_alert_when_score_drops_more_than_5_pct(db):
    """Previous=4.5 → current=4.0 → drop=11% > 5% → drift_alert=True."""
    from datetime import timedelta

    from luana_core_platform.domain.datetime_utils import utc_now

    previous_start = utc_now() - timedelta(days=14)
    previous_end = utc_now() - timedelta(days=7)
    db.add(
        SalesAgentWorkflowMetricModel(
            tenant_id=SENTINEL_TENANT_ID,
            bucket_id="qualification",
            period_start=previous_start,
            period_end=previous_end,
            started_count=3,
            judge_avg_score=4.5,
            judge_sample_size=3,
            extra_metadata={},
        ),
    )
    db.commit()

    judge = SalesAgentJudge(llm=_ScoredStubLLM(score=4.0))
    run_weekly_quality_eval(db, judge=judge)

    row = (
        db.execute(
            select(SalesAgentWorkflowMetricModel).where(
                SalesAgentWorkflowMetricModel.bucket_id == "qualification",
                SalesAgentWorkflowMetricModel.period_start > previous_start,
            ),
        )
        .scalars()
        .first()
    )
    assert row is not None, "No se persistió la fila de la semana actual."
    drop = (4.5 - 4.0) / 4.5
    assert drop > DRIFT_THRESHOLD
    assert row.extra_metadata.get("drift_alert") is True
    assert row.extra_metadata.get("drift_pct") is not None


def test_drift_detection_silent_when_score_stable(db):
    """Previous=4.0 → current=4.0 → no drift, no alert."""
    from datetime import timedelta

    from luana_core_platform.domain.datetime_utils import utc_now

    previous_start = utc_now() - timedelta(days=14)
    previous_end = utc_now() - timedelta(days=7)
    db.add(
        SalesAgentWorkflowMetricModel(
            tenant_id=SENTINEL_TENANT_ID,
            bucket_id="qualification",
            period_start=previous_start,
            period_end=previous_end,
            started_count=3,
            judge_avg_score=4.0,
            judge_sample_size=3,
            extra_metadata={},
        ),
    )
    db.commit()

    judge = SalesAgentJudge(llm=_ScoredStubLLM(score=4.0))
    run_weekly_quality_eval(db, judge=judge)

    row = (
        db.execute(
            select(SalesAgentWorkflowMetricModel).where(
                SalesAgentWorkflowMetricModel.bucket_id == "qualification",
                SalesAgentWorkflowMetricModel.period_start > previous_start,
            ),
        )
        .scalars()
        .first()
    )
    assert row is not None
    assert not row.extra_metadata.get("drift_alert")


def test_cron_registered_in_worker_settings():
    """Smoke check — el cron está registrado en SchedulerSettings.cron_jobs."""
    from src.workers.settings import SchedulerSettings

    cron_funcs = []
    for cron_job in SchedulerSettings.cron_jobs:
        coro = getattr(cron_job, "coroutine", None) or getattr(cron_job, "func", None)
        if coro is not None:
            cron_funcs.append(getattr(coro, "__name__", repr(coro)))
    assert "weekly_sales_agent_quality_eval" in cron_funcs


def test_function_registered_in_worker_settings():
    """Smoke check — el task está en WorkerSettings.functions."""
    from src.workers.settings import SchedulerSettings, WorkerSettings

    worker_funcs = {getattr(f, "__name__", repr(f)) for f in WorkerSettings.functions}
    scheduler_funcs = {getattr(f, "__name__", repr(f)) for f in SchedulerSettings.functions}
    assert "weekly_sales_agent_quality_eval" in worker_funcs
    assert "weekly_sales_agent_quality_eval" in scheduler_funcs
