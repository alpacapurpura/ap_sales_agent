"""Tests for the cost calculator.

Pure function over token counts and a pricing snapshot. Decimal in /
Decimal out — the callback handler persists the result as
``cost_usd NUMERIC(16,10)`` so we cannot leak float rounding into the
DB.
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock


def _snapshot(*, input_cost="0.0000025", output_cost="0.000010", cache_read="0.00000125"):
    snap = MagicMock()
    snap.input_cost_per_token = Decimal(input_cost)
    snap.output_cost_per_token = Decimal(output_cost)
    snap.cache_read_cost_per_token = Decimal(cache_read)
    snap.cache_write_cost_per_token = Decimal(0)
    return snap


class TestCostCalculator:
    def test_basic_call_uses_full_input_pricing(self) -> None:
        from luana_core_observability.cost.calculator import calculate_cost

        cost = calculate_cost(
            input_tokens=1000,
            output_tokens=500,
            cached_read_tokens=0,
            cached_write_tokens=0,
            pricing=_snapshot(),
        )
        # 1000 * 2.5e-6 + 500 * 1e-5 = 0.0025 + 0.005 = 0.0075
        assert cost == Decimal("0.007500000000")

    def test_cached_tokens_priced_at_cache_rate_not_input_rate(self) -> None:
        from luana_core_observability.cost.calculator import calculate_cost

        # Cached reads are subtracted from the full-priced input bucket
        # and re-added at the discounted cache_read rate. So total input
        # tokens (including cached) = 1000; uncached = 800; cached = 200.
        cost = calculate_cost(
            input_tokens=1000,
            output_tokens=500,
            cached_read_tokens=200,
            cached_write_tokens=0,
            pricing=_snapshot(),
        )
        # 800 * 2.5e-6 + 200 * 1.25e-6 + 500 * 1e-5
        # = 0.002 + 0.00025 + 0.005 = 0.00725
        assert cost == Decimal("0.007250000000")

    def test_zero_tokens_zero_cost(self) -> None:
        from luana_core_observability.cost.calculator import calculate_cost

        cost = calculate_cost(
            input_tokens=0,
            output_tokens=0,
            cached_read_tokens=0,
            cached_write_tokens=0,
            pricing=_snapshot(),
        )
        assert cost == Decimal(0)

    def test_cached_writes_billed_separately(self) -> None:
        from luana_core_observability.cost.calculator import calculate_cost

        snap = MagicMock()
        snap.input_cost_per_token = Decimal("0.000003")
        snap.output_cost_per_token = Decimal("0.000015")
        snap.cache_read_cost_per_token = Decimal("0.0000003")
        snap.cache_write_cost_per_token = Decimal("0.00000375")

        cost = calculate_cost(
            input_tokens=1000,
            output_tokens=200,
            cached_read_tokens=0,
            cached_write_tokens=300,
            pricing=snap,
        )
        # 1000 * 3e-6 + 300 * 3.75e-6 + 200 * 1.5e-5
        # = 0.003 + 0.001125 + 0.003 = 0.007125
        assert cost == Decimal("0.007125000000")

    def test_returns_decimal_not_float(self) -> None:
        from luana_core_observability.cost.calculator import calculate_cost

        cost = calculate_cost(
            input_tokens=10,
            output_tokens=10,
            cached_read_tokens=0,
            cached_write_tokens=0,
            pricing=_snapshot(),
        )
        assert isinstance(cost, Decimal)
