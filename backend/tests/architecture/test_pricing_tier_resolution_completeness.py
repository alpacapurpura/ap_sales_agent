"""Arch ratchet — calculator must implement LiteLLM tier pricing (S12).

LiteLLM declares ``input_cost_per_token_above_200k_tokens`` /
``output_cost_per_token_above_200k_tokens`` for models like Vertex AI
Gemini 3 Pro and the new long-context Anthropic / OpenAI tiers. Long
LATAM conversations or RAG-heavy prompts can cross the 200k threshold;
without tier resolution, ``cost_usd`` undercounts past that point.

This ratchet keeps ``calculate_cost`` honest: the file MUST mention the
tier keys and the threshold constant. Behavior is exercised by
``tests/shared/agent_observability/cost/test_calculator_tier_pricing.py``.
A future refactor that removes the tier path either passes both gates
or the ratchet flags it.

Watchpoint cierra: ``[MEDIUM] LiteLLM tier pricing > 200k tokens`` (S2).

# [SALES-AGENT-COST-TIER-S12] -> docs/domains/sales-agent/redesign-2026-04/phases/S12-final-hardening-zero-debt.md
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CALCULATOR_PATH = REPO_ROOT / "src" / "shared" / "agent_observability" / "cost" / "calculator.py"


@pytest.fixture(scope="module")
def calculator_source() -> str:
    return CALCULATOR_PATH.read_text(encoding="utf-8")


class TestPricingTierResolutionCompleteness:
    def test_calculator_module_exists(self) -> None:
        assert CALCULATOR_PATH.is_file(), f"calculator.py missing at {CALCULATOR_PATH}"

    def test_calculator_references_input_tier_key(self, calculator_source: str) -> None:
        assert "input_cost_per_token_above_200k_tokens" in calculator_source

    def test_calculator_references_output_tier_key(self, calculator_source: str) -> None:
        assert "output_cost_per_token_above_200k_tokens" in calculator_source

    def test_calculator_declares_tier_threshold_constant(self, calculator_source: str) -> None:
        assert "TIER_THRESHOLD" in calculator_source
        assert "200_000" in calculator_source or "200000" in calculator_source

    def test_calculator_exports_tier_threshold(self) -> None:
        from luana_core_observability.cost import calculator

        assert hasattr(calculator, "TIER_THRESHOLD")
        assert calculator.TIER_THRESHOLD == 200_000
        assert "TIER_THRESHOLD" in calculator.__all__
