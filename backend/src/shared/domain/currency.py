"""Centralized currency definitions and conversion utilities.

Single source of truth -- frontend mirrors these in currencies.ts.
"""

from dataclasses import dataclass

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
    },
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


def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
) -> float | None:
    """Convert between any two supported currencies via USD as pivot.

    Returns None if either currency has no known exchange rate.
    """
    if from_currency == to_currency:
        return round(amount, 2)
    rate_from = EXCHANGE_RATES_TO_USD.get(from_currency)
    rate_to = EXCHANGE_RATES_TO_USD.get(to_currency)
    if rate_from is None or rate_to is None or rate_to == 0:
        return None
    usd_amount = amount * rate_from
    return round(usd_amount / rate_to, 2)


@dataclass(frozen=True)
class MoneyDisplay:
    """Pre-computed amounts for frontend single-source dual display."""

    source_amount: float
    source_currency: str
    tenant_amount: float | None
    tenant_currency: str
    usd_amount: float | None


def build_money_display(
    amount: float,
    source_currency: str,
    tenant_currency: str,
) -> MoneyDisplay:
    """Build display amounts for a single-source monetary value.

    Rules:
    - source == tenant: show once (no conversion needed)
    - source != tenant: show source + tenant equivalent
    - If neither is USD: also include USD equivalent
    """
    if source_currency == tenant_currency:
        return MoneyDisplay(
            source_amount=amount,
            source_currency=source_currency,
            tenant_amount=None,
            tenant_currency=tenant_currency,
            usd_amount=None,
        )

    tenant_amount = convert_currency(amount, source_currency, tenant_currency)
    need_usd = source_currency != "USD" and tenant_currency != "USD"
    usd_amount = convert_to_usd(amount, source_currency) if need_usd else None

    return MoneyDisplay(
        source_amount=amount,
        source_currency=source_currency,
        tenant_amount=tenant_amount,
        tenant_currency=tenant_currency,
        usd_amount=usd_amount,
    )


@dataclass(frozen=True)
class AggregatedMoneyDisplay:
    """Pre-computed amounts for frontend multi-source aggregated display."""

    tenant_amount: float
    tenant_currency: str
    usd_amount: float | None


def build_aggregated_display(
    amounts: list[tuple[float, str]],
    tenant_currency: str,
) -> AggregatedMoneyDisplay:
    """Sum amounts from multiple currencies into tenant currency + USD.

    Rules:
    - All amounts converted to tenant currency and summed
    - USD shown unless tenant currency IS USD
    """
    tenant_total = 0.0
    usd_total = 0.0

    for amount, currency in amounts:
        converted = convert_currency(amount, currency, tenant_currency)
        tenant_total += converted if converted is not None else 0.0
        usd = convert_to_usd(amount, currency)
        usd_total += usd if usd is not None else 0.0

    tenant_total = round(tenant_total, 2)
    usd_total = round(usd_total, 2)

    return AggregatedMoneyDisplay(
        tenant_amount=tenant_total,
        tenant_currency=tenant_currency,
        usd_amount=usd_total if tenant_currency != "USD" else None,
    )
