"""F9 — weekly_copilot_quality_eval ARQ task contract.

# [COPILOT-LLM-JUDGE-F9]
"""

from __future__ import annotations

import json
from datetime import timedelta
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage

from src.modules.copilot.application.observability.judge import CopilotJudge
from src.modules.copilot.infrastructure.models.conversation_model import (
    CopilotConversationModel,
)
from src.modules.copilot.infrastructure.repositories.workflow_metric_repository import (
    WorkflowMetricRepository,
)
from src.shared.domain.datetime_utils import utc_now
from src.shared.workers.copilot_quality_eval import (
    NO_WORKFLOW_BUCKET,
    run_weekly_quality_eval,
)


class _StubJudgeLLM:
    def invoke(self, _messages):
        payload = {
            "accuracy": {"score": 4.0, "reason": "stub"},
            "brand_coherence": {"score": 4.0, "reason": "stub"},
            "tone": {"score": 4.0, "reason": "stub"},
            "utility": {"score": 4.0, "reason": "stub"},
        }
        return AIMessage(content=json.dumps(payload), response_metadata={"id": "x"})


def _make_conversation(
    db,
    *,
    tenant_id,
    workflow_id: str | None = "setup_brand_minimal",
    messages_count: int = 4,
):
    msgs = []
    for i in range(messages_count // 2):
        msgs.append({"role": "user", "content": f"hola {i}"})
        msgs.append({"role": "assistant", "content": f"respuesta {i}"})
    wf_state = {"workflow_id": workflow_id} if workflow_id else None
    conv = CopilotConversationModel(
        id=uuid4(),
        tenant_id=tenant_id,
        user_id=uuid4(),
        title="t",
        messages=msgs,
        workflow_state=wf_state,
    )
    db.add(conv)
    db.commit()
    return conv


def test_run_weekly_quality_eval_writes_metric_rows(db):
    tenant_a = uuid4()
    tenant_b = uuid4()
    _make_conversation(db, tenant_id=tenant_a, workflow_id="setup_brand_minimal")
    _make_conversation(db, tenant_id=tenant_a, workflow_id="setup_brand_minimal")
    _make_conversation(db, tenant_id=tenant_b, workflow_id="design_offer_from_url")

    judge = CopilotJudge(llm=_StubJudgeLLM())
    written = run_weekly_quality_eval(db, judge=judge)

    assert written == 2  # one row per (tenant, workflow_id)

    repo = WorkflowMetricRepository(db)
    rows_a = repo.list_for_tenant(tenant_id=tenant_a)
    assert len(rows_a) == 1
    assert rows_a[0].workflow_id == "setup_brand_minimal"
    assert rows_a[0].judge_sample_size == 2
    assert rows_a[0].judge_avg_score == pytest.approx(4.0, abs=0.01)


def test_run_weekly_quality_eval_buckets_no_workflow(db):
    tenant = uuid4()
    _make_conversation(db, tenant_id=tenant, workflow_id=None)
    judge = CopilotJudge(llm=_StubJudgeLLM())
    run_weekly_quality_eval(db, judge=judge)
    repo = WorkflowMetricRepository(db)
    rows = repo.list_for_tenant(tenant_id=tenant)
    assert rows[0].workflow_id == NO_WORKFLOW_BUCKET


def test_run_weekly_quality_eval_no_op_when_no_recent_conversations(db):
    judge = CopilotJudge(llm=_StubJudgeLLM())
    written = run_weekly_quality_eval(db, judge=judge)
    assert written == 0


def test_run_weekly_quality_eval_skips_old_conversations(db):
    """Conversations older than the 7-day window are excluded from sampling."""
    tenant = uuid4()
    conv = _make_conversation(db, tenant_id=tenant, workflow_id="x")
    conv.updated_at = utc_now() - timedelta(days=30)
    db.commit()
    judge = CopilotJudge(llm=_StubJudgeLLM())
    written = run_weekly_quality_eval(db, judge=judge)
    assert written == 0
