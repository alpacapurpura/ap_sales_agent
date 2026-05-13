"""F9 — WorkflowMetricRepository contract."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from luana_core_copilot.infrastructure.repositories.workflow_metric_repository import (
    WorkflowMetricRepository,
)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def period_window():
    end = datetime(2026, 4, 25, tzinfo=timezone.utc)
    start = end - timedelta(days=7)
    return start, end


def test_upsert_inserts_new_row(db, tenant_id, period_window):
    start, end = period_window
    repo = WorkflowMetricRepository(db)
    repo.upsert(
        tenant_id=tenant_id,
        workflow_id="setup_brand_minimal",
        period_start=start,
        period_end=end,
        started_count=10,
        completed_count=7,
        abandoned_count=2,
        avg_turns_to_completion=4.5,
        accept_rate=0.8,
        judge_avg_score=4.1,
        judge_sample_size=15,
        extra_metadata={"judge_model": "nano", "response_id": "resp_abc123"},
    )
    rows = repo.list_for_tenant(tenant_id=tenant_id)
    assert len(rows) == 1
    row = rows[0]
    assert row.workflow_id == "setup_brand_minimal"
    assert row.started_count == 10
    assert row.completed_count == 7
    assert row.judge_avg_score == pytest.approx(4.1, abs=0.01)
    assert row.extra_metadata == {"judge_model": "nano", "response_id": "resp_abc123"}


def test_upsert_idempotent_on_natural_key(db, tenant_id, period_window):
    start, end = period_window
    repo = WorkflowMetricRepository(db)
    repo.upsert(
        tenant_id=tenant_id,
        workflow_id="design_offer_from_url",
        period_start=start,
        period_end=end,
        started_count=5,
        completed_count=2,
        abandoned_count=3,
    )
    repo.upsert(
        tenant_id=tenant_id,
        workflow_id="design_offer_from_url",
        period_start=start,
        period_end=end,
        started_count=8,
        completed_count=4,
        abandoned_count=4,
    )
    rows = repo.list_for_tenant(tenant_id=tenant_id)
    assert len(rows) == 1
    assert rows[0].started_count == 8
    assert rows[0].completed_count == 4


def test_list_filters_by_tenant(db, tenant_id, period_window):
    start, end = period_window
    other_tenant = uuid4()
    repo = WorkflowMetricRepository(db)
    repo.upsert(
        tenant_id=tenant_id,
        workflow_id="wf_a",
        period_start=start,
        period_end=end,
        started_count=1,
        completed_count=1,
        abandoned_count=0,
    )
    repo.upsert(
        tenant_id=other_tenant,
        workflow_id="wf_a",
        period_start=start,
        period_end=end,
        started_count=99,
        completed_count=99,
        abandoned_count=0,
    )
    rows = repo.list_for_tenant(tenant_id=tenant_id)
    assert len(rows) == 1
    assert rows[0].started_count == 1
