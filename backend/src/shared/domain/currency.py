"""
Centralized currency definitions and conversion utilities.
Single source of truth -- frontend mirrors these in currencies.ts.
"""

SUPPORTED_CURRENCIES: frozenset[str] = frozenset(
    {
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
)

# Approximate static rates TO USD (multiply amount * rate = USD value)
EXCHANGE_RATES_TO_USD: dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,
    "MXN": 0.058,
    "COP": 0.00024,
    "ARS": 0.0011,
    "BRL": 0.19,
    "PEN": 0.27,
    "CLP": 0.0011,
    "GBP": 1.27,
    "CAD": 0.74,
    "AUD": 0.66,
    "JPY": 0.0067,
    "CNY": 0.14,
}


def convert_to_usd(amount: float, currency: str) -> float | None:
    """Convert amount to USD using static rates. Returns None if rate unknown."""
    rate = EXCHANGE_RATES_TO_USD.get(currency)
    if rate is None:
        return None
    return round(amount * rate, 2)


def is_valid_currency(code: str) -> bool:
    """Check if a currency code is supported."""
    return code in SUPPORTED_CURRENCIES
