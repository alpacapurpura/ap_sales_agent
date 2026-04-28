"""S10 — golden runner over 20 sales conversations.

# [SALES-AGENT-QUALITY-S10] -> docs/domains/sales-agent/redesign-2026-04/phases/S10-quality-eval-loop.md

Cada golden alimenta SalesAgentJudge. Default = stub (avg 4.0/dim → todos
pasan, pipeline integration test). RUN_LLM_JUDGE=1 invoca NANO real (cron
weekly), las regresiones surgen como fallos.
"""

from __future__ import annotations

import pytest

from src.modules.sales_agent.application.quality.judge import (
    DEFAULT_THRESHOLD,
    SalesAgentJudge,
)
from tests.quality.sales_agent_goldens.conversations import (
    CATEGORIES,
    GOLDEN_CONVERSATIONS,
    SalesAgentGolden,
)


def test_golden_dataset_has_at_least_20_conversations():
    """Phase S10 — baseline ~20 goldens cubriendo 6 categorías."""
    assert len(GOLDEN_CONVERSATIONS) >= 20


def test_golden_dataset_covers_all_required_categories():
    found = {c.category for c in GOLDEN_CONVERSATIONS}
    assert found == set(CATEGORIES), f"Missing or extra categories: expected {CATEGORIES}, got {sorted(found)}"


def test_golden_ids_unique():
    ids = [c.id for c in GOLDEN_CONVERSATIONS]
    assert len(ids) == len(set(ids))


def test_goldens_cover_multi_channel_minimum_set():
    """Phase S10 — cobertura multi-canal: whatsapp / telegram / ig / web / sms / email."""
    channels = {c.channel for c in GOLDEN_CONVERSATIONS}
    required = {"whatsapp", "telegram", "instagram_dm", "web_chat", "sms", "email"}
    missing = required - channels
    assert not missing, f"Missing channels in goldens: {missing}"


def test_goldens_cover_brand_voice_diff_pair():
    """Tenant A (formal) vs B (voseo) con mismo input — cache invariance."""
    diff_inputs = [c.user_input for c in GOLDEN_CONVERSATIONS if c.category == "brand_voice_diff"]
    duplicates = [inp for inp in diff_inputs if diff_inputs.count(inp) >= 2]
    assert duplicates, "brand_voice_diff requiere ≥2 entries con mismo user_input + brand_voice distinto"


@pytest.mark.parametrize(
    "conv",
    GOLDEN_CONVERSATIONS,
    ids=lambda c: c.id,
)
def test_golden_conversation_judges_above_threshold(
    conv: SalesAgentGolden,
    sales_judge_llm,
):
    """Pipeline test — cada golden debe ser juzgado ≥3.5/5 por el LLM activo.

    Stub mode (default): 4.0 → todos pasan.
    Real mode (``RUN_LLM_JUDGE=1``): regresiones genuinas surgen como fallos.
    """
    judge = SalesAgentJudge(llm=sales_judge_llm)
    result = judge.evaluate(
        user_input=conv.user_input,
        assistant_output=conv.expected_output,
        brand_voice=conv.brand_voice,
        channel=conv.channel,
        stage=conv.stage,
        context=conv.context,
    )
    assert result.passes_threshold, (
        f"Golden {conv.id!r} judged below threshold {DEFAULT_THRESHOLD}: "
        f"avg={result.avg_score} dims={[d.score for d in result.dimensions]} "
        f"meta={result.metadata}"
    )
