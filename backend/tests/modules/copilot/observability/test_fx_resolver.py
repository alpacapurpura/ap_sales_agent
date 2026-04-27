"""Tests for the FX resolver (USD → tenant currency)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import MagicMock


def _frankfurter_response(rates: dict[str, float], date: str = "2026-04-26"):
    """Build an httpx-like response matching frankfurter.dev /v1/latest."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "amount": 1,
        "base": "USD",
        "date": date,
        "rates": rates,
    }
    response.raise_for_status = MagicMock()
    return response


class TestFXResolver:
    def test_usd_returns_one_without_calling_api(self) -> None:
        from src.modules.copilot.observability.cost.fx_resolver import FXResolver

        client = MagicMock()
        resolver = FXResolver(http_client_factory=lambda: client)
        rate, source = resolver.resolve(
            currency_code="USD",
            at_ts=dt.datetime(2026, 4, 26, tzinfo=dt.UTC),
        )
        assert rate == Decimal(1)
        assert source == "passthrough"
        client.get.assert_not_called()

    def test_supported_currency_calls_api_and_caches(self) -> None:
        from src.modules.copilot.observability.cost.fx_resolver import FXResolver

        client = MagicMock()
        client.get.return_value = _frankfurter_response({"MXN": 17.45, "BRL": 5.10})

        resolver = FXResolver(http_client_factory=lambda: client)
        rate1, source1 = resolver.resolve(
            currency_code="MXN",
            at_ts=dt.datetime(2026, 4, 26, tzinfo=dt.UTC),
        )
        rate2, _ = resolver.resolve(
            currency_code="MXN",
            at_ts=dt.datetime(2026, 4, 26, tzinfo=dt.UTC),
        )
        assert rate1 == Decimal("17.45")
        assert rate2 == Decimal("17.45")
        assert source1 == "frankfurter"
        # One API call thanks to the daily cache.
        assert client.get.call_count == 1

    def test_unsupported_currency_returns_one_with_unsupported_source(self) -> None:
        from src.modules.copilot.observability.cost.fx_resolver import FXResolver

        client = MagicMock()
        # Frankfurter doesn't list PEN — Frankfurter's rate dict won't contain it.
        client.get.return_value = _frankfurter_response({"MXN": 17.45})

        resolver = FXResolver(http_client_factory=lambda: client)
        rate, source = resolver.resolve(
            currency_code="PEN",
            at_ts=dt.datetime(2026, 4, 26, tzinfo=dt.UTC),
        )
        # Fallback: USD passthrough + flag in source so reports can hide /
        # warn about it.
        assert rate == Decimal(1)
        assert source == "fx_unsupported"

    def test_network_error_returns_one_with_unavailable_source(self) -> None:
        from src.modules.copilot.observability.cost.fx_resolver import FXResolver

        client = MagicMock()
        client.get.side_effect = RuntimeError("network down")

        resolver = FXResolver(http_client_factory=lambda: client)
        rate, source = resolver.resolve(
            currency_code="MXN",
            at_ts=dt.datetime(2026, 4, 26, tzinfo=dt.UTC),
        )
        assert rate == Decimal(1)
        assert source == "fx_unavailable"

    def test_cache_keyed_by_date_not_full_timestamp(self) -> None:
        """Two calls on the same day with different times share a cache entry."""
        from src.modules.copilot.observability.cost.fx_resolver import FXResolver

        client = MagicMock()
        client.get.return_value = _frankfurter_response({"MXN": 17.45})

        resolver = FXResolver(http_client_factory=lambda: client)
        resolver.resolve(currency_code="MXN", at_ts=dt.datetime(2026, 4, 26, 9, 0, tzinfo=dt.UTC))
        resolver.resolve(currency_code="MXN", at_ts=dt.datetime(2026, 4, 26, 22, 0, tzinfo=dt.UTC))
        assert client.get.call_count == 1
