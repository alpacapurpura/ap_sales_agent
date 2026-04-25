"""F10 — golden RAG retrieval regression set.

Each golden row pairs a user question with: (a) the curated source doc the
KB *should* surface, and (b) the methodology the LLM is expected to cite
in its answer. The judge dimensions are RAG-specific:
``retrieval_relevance``, ``citation_accuracy``, ``answer_groundedness``,
``completeness``.

By default the judge LLM is stubbed (returns 4.0 across dims) — same
``stub default + RUN_LLM_JUDGE=1`` opt-in pattern F9 cemented. The
weekly cron flips to real NANO; CI default keeps cost at 0.

F11.5: the canonical golden corpus (``RAG_GOLDENS``, ``RagGolden``,
``RAG_DIMENSIONS``, ``METHODOLOGY_LABEL``) lives in
``src/modules/copilot/application/observability/rag_goldens.py`` so the
weekly ARQ cron can iterate the corpus without importing test code.

# [COPILOT-MARKETING-KB-F10]
"""

from __future__ import annotations

import pytest

from src.modules.copilot.application.observability.judge import (
    DEFAULT_THRESHOLD,
    CopilotJudge,
)
from src.modules.copilot.application.observability.rag_goldens import (
    METHODOLOGY_LABEL as _METHODOLOGY_LABEL,
)
from src.modules.copilot.application.observability.rag_goldens import (
    RAG_DIMENSIONS,
    RAG_GOLDENS,
    RagGolden,
)
from src.modules.copilot.application.tools.knowledge_search import (
    knowledge_search_impl,
)

# Backwards-compat alias for any external reference; the ARQ cron uses
# ``RAG_GOLDENS`` directly from the src/ module.
GOLDENS: tuple[RagGolden, ...] = RAG_GOLDENS

# Re-export so legacy imports of ``RAG_DIMENSIONS`` from this test module
# keep working.
__all__ = ("GOLDENS", "RAG_DIMENSIONS")


def _stub_chunks_for(golden: RagGolden) -> list[dict]:
    base = [
        {
            "id": f"{golden.id}-0",
            "score": 0.91,
            "content": golden.expected_answer_excerpt,
            "category": "framework",
            "methodology": golden.expected_methodology,
            "domain": "offer",
            "breadcrumb": [golden.expected_source_doc.replace(".md", "").replace("_", " ")],
            "source_doc": golden.expected_source_doc,
            "chunk_index": 0,
            "tags": [],
        }
    ]
    base.extend(golden.extra_chunks)
    return base


class _StubStore:
    """In-test store that returns the golden's expected chunk on demand."""

    def __init__(self, golden: RagGolden) -> None:
        self.golden = golden

    def search(
        self,
        query: str,
        *,
        domain: str | None = None,
        methodology: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        return _stub_chunks_for(self.golden)


def test_rag_dataset_size() -> None:
    """Keep at least 8 goldens covering the canonical methodologies."""
    assert len(GOLDENS) >= 8
    methodologies = {g.expected_methodology for g in GOLDENS}
    expected_subset = {"hormozi", "storybrand", "cialdini", "aida", "jtbd", "4u", "nicolify_owned"}
    assert expected_subset <= methodologies


def test_rag_golden_ids_unique() -> None:
    ids = [g.id for g in GOLDENS]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.id)
def test_knowledge_search_returns_expected_methodology(golden: RagGolden) -> None:
    """The tool wrapper must surface the methodology label so the LLM cites it."""
    store = _StubStore(golden)
    output = knowledge_search_impl(golden.question, store=store)
    assert "Cita el método" in output
    # methodology label must appear in the formatted markdown so the LLM
    # can pick it up when synthesising the answer.
    assert _METHODOLOGY_LABEL[golden.expected_methodology] in output


@pytest.mark.parametrize("golden", GOLDENS, ids=lambda g: g.id)
def test_rag_answer_judged_above_threshold(golden: RagGolden, judge_llm) -> None:
    """The judged answer (with retrieved context) must score ≥3.5/5.

    Pipeline test in stub mode (default 4.0 across dims). Real NANO when
    ``RUN_LLM_JUDGE=1`` is set — surfaces genuine groundedness regressions.
    """
    judge = CopilotJudge(llm=judge_llm)
    retrieved = knowledge_search_impl(golden.question, store=_StubStore(golden))
    result = judge.evaluate(
        user_input=golden.question,
        assistant_output=golden.expected_answer_excerpt,
        context=retrieved,
    )
    assert result.passes_threshold, (
        f"RAG golden {golden.id!r} judged below threshold {DEFAULT_THRESHOLD}: "
        f"avg={result.avg_score} dims={[d.score for d in result.dimensions]} "
        f"meta={result.metadata}"
    )
