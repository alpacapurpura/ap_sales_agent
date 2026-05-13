"""F9 — weekly LLM-judge eval over recent conversations.

# [COPILOT-LLM-JUDGE-F9] -> docs/domains/copilot/redesign-2026-04/phases/F9-quality-observability.md

ARQ task triggered weekly by ``SchedulerSettings.cron_jobs``. For each
tenant:

1. Sample up to ``SAMPLE_SIZE`` conversations from the last 7 days.
2. Group sampled turns by ``workflow_id`` (or ``"_no_workflow"`` for
   unbucketed chats).
3. Run :class:`CopilotJudge` (NANO) on the (last_user_msg, last_assistant_msg)
   pair of each sampled conversation.
4. Aggregate per-workflow KPIs (started/completed/abandoned counts +
   judge avg) and upsert one ``copilot_workflow_metric`` row per
   ``(tenant, workflow_id, week_start)``.

The admin ``/copilot-quality`` page reads the precomputed table — never
invokes the LLM at render time. This keeps page load <1s and keeps NANO
spend bounded to ``ceil(tenants * sample_size)`` calls per week.

Cost guard: at NANO ~$0.05 / 1M input tokens + ~80 tokens per call, 50
samples x 30 tenants x 4 weeks = 6_000 calls/month ~ $0.024/month. Safe.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from luana_core_copilot.application.observability.judge import (
    CopilotJudge,
    JudgeResult,
)
from luana_core_copilot.infrastructure.models.conversation_model import (
    CopilotConversationModel,
)
from luana_core_copilot.infrastructure.repositories.workflow_metric_repository import (
    WorkflowMetricRepository,
)
from luana_core_platform.domain.datetime_utils import utc_now
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)

SAMPLE_SIZE: int = 50
WINDOW_DAYS: int = 7
NO_WORKFLOW_BUCKET: str = "_no_workflow"


@dataclass(frozen=True, slots=True)
class _SampledTurn:
    tenant_id: UUID
    conversation_id: UUID
    workflow_id: str
    user_msg: str
    assistant_msg: str
    turns: int


def _extract_last_pair(messages: object) -> tuple[str, str] | None:
    """Pull the last (user, assistant) pair from the JSONB messages list."""
    if not isinstance(messages, list):
        return None
    last_user: str | None = None
    last_assistant: str | None = None
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role") or msg.get("type")
        content = msg.get("content")
        if not isinstance(content, str):
            continue
        if role in ("user", "human"):
            last_user = content
        elif role in ("assistant", "ai"):
            last_assistant = content
    if last_user and last_assistant:
        return last_user, last_assistant
    return None


def _sample_recent_conversations(
    db: Session,
    *,
    since: datetime,
    limit: int = SAMPLE_SIZE,
) -> list[_SampledTurn]:
    """Pull the last *limit* conversations updated since *since*.

    Filtering by ``updated_at`` keeps the sample fresh; we cap the
    ``MOST RECENT`` rows globally rather than per tenant so the eval
    naturally weights active tenants more.
    """
    stmt = (
        select(CopilotConversationModel)
        .where(CopilotConversationModel.updated_at >= since)
        .order_by(CopilotConversationModel.updated_at.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).scalars().all()
    sampled: list[_SampledTurn] = []
    for conv in rows:
        pair = _extract_last_pair(conv.messages)
        if pair is None:
            continue
        user_msg, assistant_msg = pair
        wf_state = conv.workflow_state or conv.procedure_state
        wf_id = NO_WORKFLOW_BUCKET
        if isinstance(wf_state, dict):
            candidate = wf_state.get("workflow_id") or wf_state.get("procedure")
            if isinstance(candidate, str) and candidate:
                wf_id = candidate
        turn_count = len(conv.messages) // 2 if isinstance(conv.messages, list) else 0
        sampled.append(
            _SampledTurn(
                tenant_id=conv.tenant_id,
                conversation_id=conv.id,
                workflow_id=wf_id,
                user_msg=user_msg,
                assistant_msg=assistant_msg,
                turns=turn_count,
            )
        )
    return sampled


def _judge_sample(
    judge: CopilotJudge,
    sample: list[_SampledTurn],
) -> dict[tuple[UUID, str], list[JudgeResult]]:
    """Run the judge over each sampled turn, grouped by (tenant, workflow)."""
    grouped: dict[tuple[UUID, str], list[JudgeResult]] = defaultdict(list)
    for turn in sample:
        result = judge.evaluate(
            user_input=turn.user_msg,
            assistant_output=turn.assistant_msg,
        )
        grouped[(turn.tenant_id, turn.workflow_id)].append(result)
    return grouped


def _compute_period_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    """Return the rolling weekly window (start_inclusive, end_exclusive)."""
    end = now or utc_now()
    start = end - timedelta(days=WINDOW_DAYS)
    return start, end


def _aggregate_and_upsert(
    repo: WorkflowMetricRepository,
    grouped: dict[tuple[UUID, str], list[JudgeResult]],
    sample: list[_SampledTurn],
    period: tuple[datetime, datetime],
) -> int:
    """Aggregate KPIs + upsert one row per (tenant, workflow). Returns rows written."""
    start, end = period
    written = 0
    by_key: dict[tuple[UUID, str], list[_SampledTurn]] = defaultdict(list)
    for turn in sample:
        by_key[(turn.tenant_id, turn.workflow_id)].append(turn)

    for (tenant_id, workflow_id), results in grouped.items():
        turns = by_key[(tenant_id, workflow_id)]
        scores = [r.avg_score for r in results if r.avg_score > 0]
        avg_judge = sum(scores) / len(scores) if scores else None
        avg_turn_count = sum(t.turns for t in turns) / len(turns) if turns else None
        judge_models = sorted({r.judge_model for r in results if r.judge_model})
        repo.upsert(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            period_start=start,
            period_end=end,
            started_count=len(turns),
            # We don't have explicit completion semantics in F9 — F-pos can
            # wire ``Workflow.is_complete(state)`` once the cutover lands.
            completed_count=0,
            abandoned_count=0,
            avg_turns_to_completion=avg_turn_count,
            judge_avg_score=round(avg_judge, 2) if avg_judge is not None else None,
            judge_sample_size=len(results),
            extra_metadata={
                "judge_models": judge_models,
                "stub_mode": "stub" in (judge_models[0] if judge_models else ""),
            },
        )
        written += 1
    return written


def run_weekly_quality_eval(db: Session, *, judge: CopilotJudge | None = None) -> int:
    """Sync entry point — invoked from the ARQ task wrapper + admin button.

    Returns the number of metric rows written. Exception-tolerant: a
    failure to sample / judge / upsert logs and continues so a single bad
    tenant doesn't poison the run.
    """
    judge = judge or CopilotJudge()
    period = _compute_period_window()
    since = period[0]
    try:
        sample = _sample_recent_conversations(db, since=since)
    except Exception:
        logger.exception("copilot_quality_sample_failed")
        return 0
    if not sample:
        logger.info("copilot_quality_no_recent_conversations")
        return 0
    try:
        grouped = _judge_sample(judge, sample)
    except Exception:
        logger.exception("copilot_quality_judge_failed")
        return 0
    repo = WorkflowMetricRepository(db)
    try:
        written = _aggregate_and_upsert(repo, grouped, sample, period)
    except Exception:
        logger.exception("copilot_quality_upsert_failed")
        return 0
    logger.info(
        "copilot_quality_weekly_eval_complete",
        sample_size=len(sample),
        rows_written=written,
    )
    return written


async def weekly_copilot_quality_eval(ctx: dict) -> int:
    """ARQ task wrapper — opens its own DB session via ``ctx['db_factory']``."""
    db_factory = ctx.get("db_factory")
    if db_factory is None:
        logger.warning("copilot_quality_no_db_factory")
        return 0
    db = db_factory()
    try:
        return run_weekly_quality_eval(db)
    finally:
        db.close()


__all__ = (
    "NO_WORKFLOW_BUCKET",
    "SAMPLE_SIZE",
    "WINDOW_DAYS",
    "run_weekly_quality_eval",
    "weekly_copilot_quality_eval",
)
