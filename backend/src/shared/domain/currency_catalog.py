"""Currency catalog — curated subset of SUPPORTED_CURRENCIES with display data.

The larger ``SUPPORTED_CURRENCIES`` frozenset is the validation gate — any
ISO 4217 code in it is accepted for storage, conversion, and display. The
catalog in this module is the **curated list surfaced in UI pickers**
(offer wizard pricing step, settings, etc.): a small, locale-targeted
subset that keeps the dropdown useful instead of showing 150 options.

Adding a new currency to the picker requires:

1. Include the code in ``SUPPORTED_CURRENCIES`` + add an
   ``EXCHANGE_RATES_TO_USD`` entry.
2. Add a ``CurrencyMetadata`` record here.

The architecture test ``test_currency_catalog_completeness`` enforces
both invariants at CI time.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CurrencyMetadata:
    """Locale-aware display data for an ISO 4217 currency code.

    ``symbol`` is what the UI renders next to the amount. Several Latin
    American currencies share ``$`` as symbol, so the picker shows both
    the ISO code and the symbol to disambiguate.
    ``decimal_digits`` is the minor-unit count — 0 for CLP / PYG,
    2 for everyone else in this catalog.
    """

    code: str  # ISO 4217, uppercase, exactly 3 letters
    label_es: str
    symbol: str
    countries_es: tuple[str, ...] = field(default_factory=tuple)
    decimal_digits: int = 2


CURRENCY_CATALOG: dict[str, CurrencyMetadata] = {
    "USD": CurrencyMetadata(
        code="USD",
        label_es="Dólar estadounidense",
        symbol="$",
        countries_es=(
            "Estados Unidos",
            "El Salvador",
        ),
        decimal_digits=2,
    ),
    "PEN": CurrencyMetadata(
        code="PEN",
        label_es="Sol peruano",
        symbol="S/",
        countries_es=("Perú",),
        decimal_digits=2,
    ),
    "ARS": CurrencyMetadata(
        code="ARS",
        label_es="Peso argentino",
        symbol="$",
        countries_es=("Argentina",),
        decimal_digits=2,
    ),
    "CLP": CurrencyMetadata(
        code="CLP",
        label_es="Peso chileno",
        symbol="$",
        countries_es=("Chile",),
        decimal_digits=0,
    ),
    "COP": CurrencyMetadata(
        code="COP",
        label_es="Peso colombiano",
        symbol="$",
        countries_es=("Colombia",),
        decimal_digits=2,
    ),
    "BOB": CurrencyMetadata(
        code="BOB",
        label_es="Boliviano",
        symbol="Bs",
        countries_es=("Bolivia",),
        decimal_digits=2,
    ),
    "UYU": CurrencyMetadata(
        code="UYU",
        label_es="Peso uruguayo",
        symbol="$U",
        countries_es=("Uruguay",),
        decimal_digits=2,
    ),
    "PYG": CurrencyMetadata(
        code="PYG",
        label_es="Guaraní paraguayo",
        symbol="₲",
        countries_es=("Paraguay",),
        decimal_digits=0,
    ),
    "MXN": CurrencyMetadata(
        code="MXN",
        label_es="Peso mexicano",
        symbol="$",
        countries_es=("México",),
        decimal_digits=2,
    ),
    "CRC": CurrencyMetadata(
        code="CRC",
        label_es="Colón costarricense",
        symbol="₡",
        countries_es=("Costa Rica",),
        decimal_digits=2,
    ),
}


def get_currency_metadata(code: str) -> CurrencyMetadata:
    """Return the metadata for a curated currency ``code``.

    Raises :class:`KeyError` for codes outside the catalog. Callers that
    want a fallback should use ``CURRENCY_CATALOG.get()`` directly.
    """
    return CURRENCY_CATALOG[code]
