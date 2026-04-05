"""Analytics domain ports — re-exported from shared for backward compatibility.

Canonical location: src.shared.domain.ports
New code should import directly from src.shared.domain.ports.
"""

from src.shared.domain.ports import (
    ConnectionCredentials,
    ConnectionPort,
    OfferReadDTO,
    OfferReadPort,
    ProductMappingPort,
)

__all__ = [
    "ConnectionCredentials",
    "ConnectionPort",
    "OfferReadDTO",
    "OfferReadPort",
    "ProductMappingPort",
]
