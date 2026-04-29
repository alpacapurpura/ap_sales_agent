"""Tier pricing tests for the cost calculator (S12).

When LiteLLM exposes ``input_cost_per_token_above_200k_tokens`` /
``output_cost_per_token_above_200k_tokens``, the calculator must split
the uncached input / output buckets at ``TIER_THRESHOLD = 200_000``
tokens. Tokens up to the threshold use the base rate; tokens past it
use the tier rate. Cache reads / writes are never split — they live in
their own buckets at their own rates.

The arch ratchet
``tests/architecture/test_pricing_tier_resolution_completeness.py``
guarantees the calculator file keeps the tier handling logic; these
tests guarantee the math.

# [SALES-AGENT-COST-TIER-S12] -> docs/domains/sales-agent/redesign-2026-04/phases/S12-final-hardening-zero-debt.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(slots=True)
class _Snap:
    """Pricing snapshot stand-in with optional tier fields + raw_payload."""

    input_cost_per_token: Decimal = Decimal("0.000003")
    output_cost_per_token: Decimal = Decimal("0.000005")
    cache_read_cost_per_token: Decimal | None = None
    cache_write_cost_per_token: Decimal | None = None
    input_cost_per_token_above_200k_tokens: Decimal | None = None
    output_cost_per_token_above_200k_tokens: Decimal | None = None
    raw_payload: dict[str, object] = field(default_factory=dict)


class TestTierResolutionInput:
    def test_no_tier_when_input_below_threshold(self) -> None:
        from src.shared.agent_observability.cost.calculator import calculate_cost

        snap = _Snap(input_cost_per_token_above_200k_tokens=Decimal("0.000004"))
        cost = calculate_cost(
            input_tokens=150_000,
            output_tokens=0,
            cached_read_tokens=0,
            cached_write_tokens=0,
            pricing=snap,
        )
        assert cost == Decimal("0.000003") * 150_000

    def test_input_tier_splits_at_200k(self) -> None:
        from src.shared.agent_observability.cost.calculator import calculate_cost

        snap = _Snap(input_cost_per_token_above_200k_tokens=Decimal("0.000004"))
        cost = calculate_cost(
            input_tokens=300_000,
            output_tokens=0,
            cached_read_tokens=0,
            cached_write_tokens=0,
            pricing=snap,
        )
        expected = Decimal("0.000003") * 200_000 + Decimal("0.000004") * 100_000
        assert cost == expected

    def test_input_tier_at_exact_threshold_uses_base_rate(self) -> None:
        from src.shared.agent_observability.cost.calculator import calculate_cost

        snap = _Snap(input_cost_per_token_above_200k_tokens=Decimal("0.000004"))
        cost = calculate_cost(
            input_tokens=200_000,
            output_tokens=0,
            cached_read_tokens=0,
            cached_write_tokens=0,
            pricing=snap,
        )
        assert cost == Decimal("0.000003") * 200_000

    def test_input_tier_resolved_from_raw_payload(self) -> None:
        from src.shared.agent_observability.cost.calculator import calculate_cost

        snap = _Snap(
            raw_payload={"input_cost_per_token_above_200k_tokens": "0.000004"},
        )
        cost = calculate_cost(
            input_tokens=300_000,
            output_tokens=0,
            cached_read_tokens=0,
            cached_write_tokens=0,
            pricing=snap,
        )
        expected = Decimal("0.000003") * 200_000 + Decimal("0.000004") * 100_000
        assert cost == expected

    def test_no_tier_when_rate_absent(self) -> None:
        from src.shared.agent_observability.cost.calculator import calculate_cost

        snap = _Snap()  # no tier rate, no raw_payload tier
        cost = calculate_cost(
            input_tokens=300_000,
            output_tokens=0,
            cached_read_tokens=0,
            cached_write_tokens=0,
            pricing=snap,
        )
        assert cost == Decimal("0.000003") * 300_000

    def test_cached_reads_subtracted_before_tier_split(self) -> None:
        from src.shared.agent_observability.cost.calculator import calculate_cost

        # 250k input, 100k cached → 150k uncached → below 200k → no tier.
        snap = _Snap(
            cache_read_cost_per_token=Decimal("0.000001"),
            input_cost_per_token_above_200k_tokens=Decimal("0.000004"),
        )
        cost = calculate_cost(
            input_tokens=250_000,
            output_tokens=0,
            cached_read_tokens=100_000,
            cached_write_tokens=0,
            pricing=snap,
        )
        # 150_000 uncached @ base + 100_000 cached @ cache rate
        expected = Decimal("0.000003") * 150_000 + Decimal("0.000001") * 100_000
        assert cost == expected

    def test_cached_reads_with_tier_when_uncached_above_threshold(self) -> None:
        from src.shared.agent_observability.cost.calculator import calculate_cost

        # 350k input, 50k cached → 300k uncached → 200k base + 100k tier.
        snap = _Snap(
            cache_read_cost_per_token=Decimal("0.000001"),
            input_cost_per_token_above_200k_tokens=Decimal("0.000004"),
        )
        cost = calculate_cost(
            input_tokens=350_000,
            output_tokens=0,
            cached_read_tokens=50_000,
            cached_write_tokens=0,
            pricing=snap,
        )
        expected = Decimal("0.000003") * 200_000 + Decimal("0.000004") * 100_000 + Decimal("0.000001") * 50_000
        assert cost == expected


class TestTierResolutionOutput:
    def test_output_tier_splits_at_200k(self) -> None:
        from src.shared.agent_observability.cost.calculator import calculate_cost

        snap = _Snap(output_cost_per_token_above_200k_tokens=Decimal("0.000010"))
        cost = calculate_cost(
            input_tokens=0,
            output_tokens=300_000,
            cached_read_tokens=0,
            cached_write_tokens=0,
            pricing=snap,
        )
        expected = Decimal("0.000005") * 200_000 + Decimal("0.000010") * 100_000
        assert cost == expected

    def test_output_tier_resolved_from_raw_payload(self) -> None:
        from src.shared.agent_observability.cost.calculator import calculate_cost

        snap = _Snap(
            raw_payload={"output_cost_per_token_above_200k_tokens": "0.000010"},
        )
        cost = calculate_cost(
            input_tokens=0,
            output_tokens=300_000,
            cached_read_tokens=0,
            cached_write_tokens=0,
            pricing=snap,
        )
        expected = Decimal("0.000005") * 200_000 + Decimal("0.000010") * 100_000
        assert cost == expected


class TestTierResolutionCombined:
    def test_input_and_output_tiers_combined(self) -> None:
        from src.shared.agent_observability.cost.calculator import calculate_cost

        snap = _Snap(
            input_cost_per_token_above_200k_tokens=Decimal("0.000004"),
            output_cost_per_token_above_200k_tokens=Decimal("0.000010"),
        )
        cost = calculate_cost(
            input_tokens=300_000,
            output_tokens=300_000,
            cached_read_tokens=0,
            cached_write_tokens=0,
            pricing=snap,
        )
        input_cost = Decimal("0.000003") * 200_000 + Decimal("0.000004") * 100_000
        output_cost = Decimal("0.000005") * 200_000 + Decimal("0.000010") * 100_000
        assert cost == input_cost + output_cost

    def test_typed_attribute_takes_precedence_over_raw_payload(self) -> None:
        from src.shared.agent_observability.cost.calculator import calculate_cost

        snap = _Snap(
            input_cost_per_token_above_200k_tokens=Decimal("0.000004"),
            raw_payload={"input_cost_per_token_above_200k_tokens": "999"},
        )
        cost = calculate_cost(
            input_tokens=300_000,
            output_tokens=0,
            cached_read_tokens=0,
            cached_write_tokens=0,
            pricing=snap,
        )
        expected = Decimal("0.000003") * 200_000 + Decimal("0.000004") * 100_000
        assert cost == expected
