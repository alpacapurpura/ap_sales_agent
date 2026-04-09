"""TenantLocale — immutable value object for tenant display preferences.

Single source of truth for 'how should this tenant see monetary amounts and dates'.
Backend stores UTC + source currency; TenantLocale drives conversion for display.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TenantLocale:
    """Immutable tenant display preferences."""

    currency: str  # ISO 4217: "PEN", "USD", "MXN"
    timezone: str  # IANA: "America/Lima", "America/Bogota"

    @classmethod
    def default(cls) -> "TenantLocale":
        """Fallback when tenant settings are unavailable."""
        return cls(currency="USD", timezone="UTC")
