"""F9 — golden semantic regression tests for 20 canonical conversations.

# [COPILOT-LLM-JUDGE-F9]

Each row in :data:`GOLDEN_CONVERSATIONS` is fed to ``CopilotJudge``. By
default the judge LLM is stubbed (returns 4.0 across dims) — this verifies
the pipeline plumbs correctly. Set ``RUN_LLM_JUDGE=1`` to invoke real
NANO; the weekly cron does this in CI.
"""

from __future__ import annotations

import pytest

from luana_core_copilot.application.observability.judge import (
    DEFAULT_THRESHOLD,
    CopilotJudge,
)
from tests.quality.golden.conversations import (
    CATEGORIES,
    GOLDEN_CONVERSATIONS,
    GoldenConversation,
)


def test_golden_dataset_has_20_conversations():
    assert len(GOLDEN_CONVERSATIONS) == 20


def test_golden_dataset_covers_8_categories():
    found = {c.category for c in GOLDEN_CONVERSATIONS}
    assert found == set(CATEGORIES), f"Missing or extra categories: expected {CATEGORIES}, got {sorted(found)}"


def test_golden_ids_unique():
    ids = [c.id for c in GOLDEN_CONVERSATIONS]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize(
    "conv",
    GOLDEN_CONVERSATIONS,
    ids=lambda c: c.id,
)
def test_golden_conversation_judges_above_threshold(conv: GoldenConversation, judge_llm):
    """Pipeline test — every golden must be judged ≥3.5/5 by the active LLM.

    In stub mode (default) every judgement is 4.0 → all pass. In real
    mode (``RUN_LLM_JUDGE=1``) genuine regressions surface as failures.
    """
    judge = CopilotJudge(llm=judge_llm)
    result = judge.evaluate(
        user_input=conv.user_input,
        assistant_output=conv.expected_output,
        brand_summary=conv.brand_summary,
        context=conv.context,
    )
    assert result.passes_threshold, (
        f"Golden {conv.id!r} judged below threshold {DEFAULT_THRESHOLD}: "
        f"avg={result.avg_score} dims={[d.score for d in result.dimensions]} "
        f"meta={result.metadata}"
    )
