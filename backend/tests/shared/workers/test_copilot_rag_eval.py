"""F11.5 — weekly_copilot_rag_eval ARQ task contract.

# [COPILOT-RAG-EVAL-F11]
"""

from __future__ import annotations

import json

import pytest
from langchain_core.messages import AIMessage

from luana_core_copilot.application.observability.judge import CopilotJudge
from luana_core_copilot.application.observability.rag_goldens import (
    RAG_DIMENSIONS,
    RAG_GOLDENS,
    RagGolden,
)
from luana_core_copilot.infrastructure.repositories.workflow_metric_repository import (
    WorkflowMetricRepository,
)
from src.shared.workers.copilot_rag_eval import (
    RAG_SENTINEL_TENANT,
    RAG_WORKFLOW_ID,
    run_weekly_rag_eval,
)


class _StubJudgeLLM:
    """Mirrors F9 stub — returns a balanced 4.0 JSON across the RAG dims."""

    def invoke(self, _messages: list) -> AIMessage:
        payload = {dim: {"score": 4.0, "reason": "stub"} for dim in RAG_DIMENSIONS}
        return AIMessage(content=json.dumps(payload), response_metadata={"id": "stub-rag"})


class _GoldenStubStore:
    """Returns the expected source doc top-1 — recall = 1.0 by default."""

    def __init__(self, *, miss_doc: str | None = None) -> None:
        self.miss_doc = miss_doc

    def search(
        self,
        query: str,
        *,
        domain: str | None = None,
        methodology: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        # Match by question prefix to find the golden being asked.
        for golden in RAG_GOLDENS:
            if golden.question == query:
                if self.miss_doc and golden.expected_source_doc == self.miss_doc:
                    # Return a chunk from a different doc → recall miss.
                    return [
                        {
                            "id": f"{golden.id}-miss",
                            "score": 0.5,
                            "content": "off-topic",
                            "category": "framework",
                            "methodology": "storybrand",
                            "domain": "brand",
                            "breadcrumb": ["other"],
                            "source_doc": "99_other.md",
                            "chunk_index": 0,
                            "tags": [],
                        },
                    ]
                return [
                    {
                        "id": f"{golden.id}-0",
                        "score": 0.92,
                        "content": golden.expected_answer_excerpt,
                        "category": "framework",
                        "methodology": golden.expected_methodology,
                        "domain": "offer",
                        "breadcrumb": [golden.expected_source_doc.replace(".md", "")],
                        "source_doc": golden.expected_source_doc,
                        "chunk_index": 0,
                        "tags": [],
                    },
                ]
        return []


@pytest.fixture
def judge() -> CopilotJudge:
    return CopilotJudge(llm=_StubJudgeLLM(), dimensions=RAG_DIMENSIONS)


def test_run_weekly_rag_eval_writes_single_aggregate_row(db, judge):
    written = run_weekly_rag_eval(db, store=_GoldenStubStore(), judge=judge)

    assert written == 1

    repo = WorkflowMetricRepository(db)
    rows = repo.list_for_tenant(tenant_id=RAG_SENTINEL_TENANT)
    assert len(rows) == 1
    row = rows[0]
    assert row.workflow_id == RAG_WORKFLOW_ID
    assert row.judge_sample_size == len(RAG_GOLDENS)
    assert row.started_count == len(RAG_GOLDENS)
    assert row.completed_count == len(RAG_GOLDENS)
    assert row.abandoned_count == 0


def test_aggregate_metadata_shape(db, judge):
    run_weekly_rag_eval(db, store=_GoldenStubStore(), judge=judge)
    rows = WorkflowMetricRepository(db).list_for_tenant(tenant_id=RAG_SENTINEL_TENANT)
    meta = rows[0].extra_metadata
    assert meta is not None
    # Required keys per F11.5 spec.
    expected_keys = {
        "golden_count",
        "retrieval_recall_avg",
        "retrieval_latency_ms_avg",
        "kb_citations",
        "judge_dimensions",
        "per_golden_recall",
        "judge_models",
        "failed_golden_ids",
    }
    assert expected_keys <= set(meta.keys())
    assert meta["retrieval_recall_avg"] == 1.0
    assert set(meta["judge_dimensions"]) == set(RAG_DIMENSIONS)
    assert all(score == 4.0 for score in meta["judge_dimensions"].values())
    assert meta["failed_golden_ids"] == []


def test_recall_drops_when_expected_doc_missing(db, judge):
    miss = RAG_GOLDENS[0].expected_source_doc
    run_weekly_rag_eval(db, store=_GoldenStubStore(miss_doc=miss), judge=judge)
    rows = WorkflowMetricRepository(db).list_for_tenant(tenant_id=RAG_SENTINEL_TENANT)
    meta = rows[0].extra_metadata
    expected = round((len(RAG_GOLDENS) - 1) / len(RAG_GOLDENS), 3)
    assert meta["retrieval_recall_avg"] == expected
    assert meta["per_golden_recall"][RAG_GOLDENS[0].id] == 0.0


def test_per_golden_failure_isolated(db, judge):
    class HalfBrokenStore:
        def __init__(self) -> None:
            self.calls = 0

        def search(self, query: str, *, limit: int = 5) -> list[dict]:
            self.calls += 1
            if self.calls == 1:
                msg = "qdrant down"
                raise RuntimeError(msg)
            for golden in RAG_GOLDENS:
                if golden.question == query:
                    return [
                        {
                            "id": f"{golden.id}-0",
                            "score": 0.9,
                            "content": golden.expected_answer_excerpt,
                            "source_doc": golden.expected_source_doc,
                            "methodology": golden.expected_methodology,
                            "category": "framework",
                            "domain": "offer",
                            "breadcrumb": [],
                            "chunk_index": 0,
                            "tags": [],
                        },
                    ]
            return []

    written = run_weekly_rag_eval(db, store=HalfBrokenStore(), judge=judge)
    assert written == 1
    rows = WorkflowMetricRepository(db).list_for_tenant(tenant_id=RAG_SENTINEL_TENANT)
    meta = rows[0].extra_metadata
    assert meta["golden_count"] == len(RAG_GOLDENS) - 1
    assert len(meta["failed_golden_ids"]) == 1


def test_no_results_returns_zero(db, judge):
    class EmptyStore:
        def search(self, *args, **kwargs) -> list[dict]:
            return []

    # All goldens succeed (no exception) but recall=0.0; still 1 row written.
    written = run_weekly_rag_eval(db, store=EmptyStore(), judge=judge)
    assert written == 1
    rows = WorkflowMetricRepository(db).list_for_tenant(tenant_id=RAG_SENTINEL_TENANT)
    assert rows[0].extra_metadata["retrieval_recall_avg"] == 0.0


def test_run_in_subset_via_goldens_arg(db, judge):
    sub: tuple[RagGolden, ...] = RAG_GOLDENS[:2]
    written = run_weekly_rag_eval(db, store=_GoldenStubStore(), judge=judge, goldens=sub)
    assert written == 1
    rows = WorkflowMetricRepository(db).list_for_tenant(tenant_id=RAG_SENTINEL_TENANT)
    assert rows[0].judge_sample_size == 2
