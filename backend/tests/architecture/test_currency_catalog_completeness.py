"""Architecture fitness: currency catalog ↔ supported currencies alignment.

The curated catalog must be a subset of SUPPORTED_CURRENCIES and every
code must have an exchange rate defined, otherwise displays / conversions
silently return ``None``. CI fails the moment either invariant breaks.
"""

from __future__ import annotations

from src.shared.domain.currency import EXCHANGE_RATES_TO_USD, SUPPORTED_CURRENCIES
from src.shared.domain.currency_catalog import CURRENCY_CATALOG


def test_every_catalog_code_is_supported() -> None:
    missing = [code for code in CURRENCY_CATALOG if code not in SUPPORTED_CURRENCIES]
    assert missing == [], (
        f"Currency catalog exposes codes that SUPPORTED_CURRENCIES does not whitelist: {missing}. "
        "Add them to SUPPORTED_CURRENCIES in shared/domain/currency.py."
    )


def test_every_catalog_code_has_exchange_rate() -> None:
    missing = [code for code in CURRENCY_CATALOG if code not in EXCHANGE_RATES_TO_USD]
    assert missing == [], (
        f"Currency catalog exposes codes without exchange rates: {missing}. "
        "Add rates to EXCHANGE_RATES_TO_USD in shared/domain/currency.py."
    )


def test_catalog_entries_self_reference_their_code() -> None:
    for code, metadata in CURRENCY_CATALOG.items():
        assert metadata.code == code, f"Catalog key {code} != metadata.code {metadata.code}"
