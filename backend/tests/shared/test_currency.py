"""Tests for shared currency module — single source of truth for currencies."""

import pytest

from src.shared.domain.currency import (
    EXCHANGE_RATES_TO_USD,
    SUPPORTED_CURRENCIES,
    convert_to_usd,
    is_valid_currency,
)

EXPECTED_CURRENCIES = {
    "USD",
    "EUR",
    "MXN",
    "COP",
    "ARS",
    "BRL",
    "PEN",
    "CLP",
    "GBP",
    "CAD",
    "AUD",
    "JPY",
    "CNY",
}


class TestSupportedCurrencies:
    """Verify the 13 supported currencies exist."""

    def test_supported_currencies_count(self) -> None:
        assert len(SUPPORTED_CURRENCIES) == 13

    def test_supported_currencies_match_expected(self) -> None:
        assert SUPPORTED_CURRENCIES == EXPECTED_CURRENCIES

    def test_supported_currencies_is_frozenset(self) -> None:
        assert isinstance(SUPPORTED_CURRENCIES, frozenset)

    @pytest.mark.parametrize("code", sorted(EXPECTED_CURRENCIES))
    def test_each_currency_in_supported(self, code: str) -> None:
        assert code in SUPPORTED_CURRENCIES


class TestExchangeRates:
    """Verify exchange rates dict covers all supported currencies."""

    def test_all_supported_currencies_have_rates(self) -> None:
        for code in SUPPORTED_CURRENCIES:
            assert code in EXCHANGE_RATES_TO_USD, f"Missing rate for {code}"

    def test_usd_rate_is_identity(self) -> None:
        assert EXCHANGE_RATES_TO_USD["USD"] == 1.0

    def test_all_rates_are_positive(self) -> None:
        for code, rate in EXCHANGE_RATES_TO_USD.items():
            assert rate > 0, f"Rate for {code} must be positive, got {rate}"


class TestConvertToUsd:
    """Verify convert_to_usd() conversion logic."""

    def test_usd_identity(self) -> None:
        result = convert_to_usd(100.0, "USD")
        assert result == 100.0

    @pytest.mark.parametrize("code", sorted(EXPECTED_CURRENCIES))
    def test_convert_all_currencies(self, code: str) -> None:
        result = convert_to_usd(1000.0, code)
        assert result is not None
        assert isinstance(result, float)
        assert result > 0

    def test_unsupported_currency_returns_none(self) -> None:
        assert convert_to_usd(100.0, "XYZ") is None

    def test_another_unsupported_currency_returns_none(self) -> None:
        assert convert_to_usd(50.0, "FAKE") is None

    def test_zero_amount(self) -> None:
        result = convert_to_usd(0.0, "MXN")
        assert result == 0.0

    def test_result_rounded_to_two_decimals(self) -> None:
        result = convert_to_usd(100.0, "MXN")
        assert result is not None
        # Check it has at most 2 decimal places
        assert result == round(result, 2)

    def test_known_conversion_mxn(self) -> None:
        """100 MXN * 0.058 = 5.8 USD."""
        result = convert_to_usd(100.0, "MXN")
        assert result == 5.8

    def test_known_conversion_eur(self) -> None:
        """100 EUR * 1.08 = 108.0 USD."""
        result = convert_to_usd(100.0, "EUR")
        assert result == 108.0


class TestIsValidCurrency:
    """Verify is_valid_currency() helper."""

    @pytest.mark.parametrize("code", sorted(EXPECTED_CURRENCIES))
    def test_valid_currencies(self, code: str) -> None:
        assert is_valid_currency(code) is True

    def test_invalid_currency(self) -> None:
        assert is_valid_currency("XYZ") is False

    def test_lowercase_is_invalid(self) -> None:
        assert is_valid_currency("usd") is False

    def test_empty_string_is_invalid(self) -> None:
        assert is_valid_currency("") is False
