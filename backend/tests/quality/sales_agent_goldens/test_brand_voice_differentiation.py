"""S10 — brand voice differentiation goldens (cache invariance).

# [SALES-AGENT-QUALITY-S10] -> docs/domains/sales-agent/redesign-2026-04/phases/S10-quality-eval-loop.md

Tenant A (formal neutro) vs Tenant B (voseo AR casual) con mismo
``user_input`` — el judge debe asignar ``brand_voice_fidelity`` distintivo
porque la rúbrica respeta lo que el tenant configuró en su brand voice.

Hoy con stub (4.0 fijo) este test sirve como contract — la diferencia se
verá empíricamente cuando ``RUN_LLM_JUDGE=1`` corra el cron weekly.
Implementación en stub: damos goldens distintos cuyo ``expected_output``
respeta su voz, y aseguramos que el judge no rechaza ninguno.
"""

from __future__ import annotations

from collections import defaultdict

from src.modules.sales_agent.application.quality.judge import SalesAgentJudge
from tests.quality.sales_agent_goldens.conversations import GOLDEN_CONVERSATIONS


def _diff_pairs() -> list[tuple]:
    """Goldens de brand_voice_diff agrupados por ``user_input``."""
    grouped: dict[str, list] = defaultdict(list)
    for conv in GOLDEN_CONVERSATIONS:
        if conv.category == "brand_voice_diff":
            grouped[conv.user_input].append(conv)
    return [tuple(pairs) for pairs in grouped.values() if len(pairs) >= 2]


def test_brand_voice_diff_pairs_share_input_but_differ_in_output(sales_judge_llm):
    """Mismo input → outputs distintos cuando la brand_voice difiere."""
    pairs = _diff_pairs()
    assert pairs, "Esperaba ≥1 par de goldens con mismo user_input + voz distinta."
    for pair in pairs:
        outputs = {c.expected_output for c in pair}
        assert len(outputs) == len(pair), (
            f"Goldens con mismo user_input deben tener expected_output distinto;"
            f" got duplicates en {[c.id for c in pair]}"
        )


def test_brand_voice_diff_judge_passes_each_variant(sales_judge_llm):
    """El judge stubbed debe aceptar cada variante (cada output respeta su voz)."""
    judge = SalesAgentJudge(llm=sales_judge_llm)
    pairs = _diff_pairs()
    assert pairs, "Esperaba goldens brand_voice_diff."
    for pair in pairs:
        for conv in pair:
            result = judge.evaluate(
                user_input=conv.user_input,
                assistant_output=conv.expected_output,
                brand_voice=conv.brand_voice,
                channel=conv.channel,
                stage=conv.stage,
            )
            assert result.passes_threshold, (
                f"Variant {conv.id!r} (voz: {conv.brand_voice[:40]}…) falló judge:"
                f" avg={result.avg_score} meta={result.metadata}"
            )


def test_brand_voice_diff_pairs_use_different_brand_voice_strings():
    """Las voces inyectadas son strings distintos — base para diff real."""
    pairs = _diff_pairs()
    for pair in pairs:
        voices = {c.brand_voice for c in pair}
        assert len(voices) == len(pair), (
            f"Pair con mismo brand_voice + mismo input — no testea diff; {[c.id for c in pair]}"
        )
