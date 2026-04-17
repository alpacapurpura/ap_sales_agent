"""Unit tests for the curated currency catalog.

The catalog is the SSoT for which currencies the wizard + pricing
selectors expose. Every code is ISO 4217 and comes with display data
(label_es, symbol, country list, minor-unit decimals).
"""

from __future__ import annotations

from src.shared.domain.currency import SUPPORTED_CURRENCIES, is_valid_currency
from src.shared.domain.currency_catalog import (
    CURRENCY_CATALOG,
    CurrencyMetadata,
    get_currency_metadata,
)


class TestCurrencyCatalog:
    def test_catalog_exposes_ten_curated_codes(self) -> None:
        expected = {
            "USD",
            "PEN",
            "ARS",
            "CLP",
            "COP",
            "BOB",
            "UYU",
            "PYG",
            "MXN",
            "CRC",
        }
        assert set(CURRENCY_CATALOG.keys()) == expected

    def test_every_catalog_code_is_supported_and_has_rate(self) -> None:
        """The catalog can only expose currencies that SUPPORTED_CURRENCIES
        already whitelists, so conversion and validation keep working."""
        for code in CURRENCY_CATALOG:
            assert is_valid_currency(code), f"{code} missing from SUPPORTED_CURRENCIES"
            assert code in SUPPORTED_CURRENCIES

    def test_every_entry_has_required_fields(self) -> None:
        for code, metadata in CURRENCY_CATALOG.items():
            assert isinstance(metadata, CurrencyMetadata)
            assert metadata.code == code
            assert len(metadata.code) == 3
            assert metadata.code.isupper()
            assert metadata.label_es.strip()
            assert metadata.symbol.strip()
            assert metadata.countries_es, f"{code} missing countries_es"
            assert metadata.decimal_digits in (0, 2), f"{code} has unusual decimals: {metadata.decimal_digits}"

    def test_usd_covers_usa_and_el_salvador(self) -> None:
        """Per the wizard requirements, USD appears once and represents both
        the USA and El Salvador (official tender since 2001)."""
        usd = get_currency_metadata("USD")
        countries = {c.lower() for c in usd.countries_es}
        assert any("estados unidos" in c for c in countries)
        assert any("salvador" in c for c in countries)

    def test_integer_currencies_declare_zero_decimals(self) -> None:
        """Chilean peso and Paraguayan guaraní don't use minor units —
        the selector must render them as integers so no phantom cents
        sneak into the DB."""
        assert get_currency_metadata("CLP").decimal_digits == 0
        assert get_currency_metadata("PYG").decimal_digits == 0
        # Spot-check a 2-decimal entry.
        assert get_currency_metadata("PEN").decimal_digits == 2

    def test_get_currency_metadata_raises_for_unknown(self) -> None:
        import pytest

        with pytest.raises(KeyError):
            get_currency_metadata("ZZZ")
